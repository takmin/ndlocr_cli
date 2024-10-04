import argparse 
from PIL import Image
from pix2tex.cli import LatexOCR
import os
import json
import copy
from read_ndlocr_xml import check_line_overlap


model = LatexOCR()

def extract_all_lines(layout_info):
    lines = []
    # Check if 'LINES' is in the top level of the dictionary
    if 'LINES' in layout_info:
        lines.extend(layout_info['LINES'])

    # Check if 'BLOCKS' is in the top level of the dictionary
    if 'BLOCKS' in layout_info:
        for block in layout_info['BLOCKS']:
            # Check if 'LINES' is in each block
            if 'LINES' in block:
                lines.extend(block['LINES']) 
    return lines


def extract_overlap_lines(lines, block):
    return [line for line in lines if(check_line_overlap(line, block) > 0.5)]


def latexocr(lines, img, margin):
    math_lines = []
    for line in lines:
        # マージンを取って画像を切り抜き
        W = line["WIDTH"]
        H = line["HEIGHT"]
        margin_h = H * margin
        left = line["X"]
        right = left + W
        top = max(int(line["Y"] - margin_h / 2), 0)
        bottom = min(int(top + H + margin_h), img.height)
        crop_img = img.crop((left, top, right, bottom))
        copy_line = copy.copy(line)
        copy_line["STRING"] = model(crop_img)
        copy_line["TYPE"] = "LaTeX-OCR"
        math_lines.append(copy_line)
    return math_lines


def recog_text_in_math(image_dir, json_dir, output_dir, threshold=0.0):
    """
    1. 画像ファイルをロード
    2. 対応するjsonファイルをロード
    3. jsonから数式領域を抽出
    4. 全LINEを抽出し、数式ブロックとのオーバーラップを判定
    5. オーバーラップしたLINEに高さ方向にマージンを取った領域で画像を切り取り
    5. 切り取った画像に対してLaTeX-OCRをかける
    6. 認識結果をjsonへ再格納
    """
    # 画像ファイル名一覧を取得
    image_files = [f for f in os.listdir(image_dir) if f.lower().endswith(('.png', '.jpeg', '.bmp', '.gif'))]

    if(not os.path.exists(output_dir)):
        os.mkdir(output_dir)
    
    for image_file in image_files:
        print("processing {}".format(image_file))
        basename_without_ext = os.path.splitext(os.path.basename(image_file))[0]
        json_file = os.path.join(json_dir, basename_without_ext + ".json")
        with open(json_file) as f:
            # jsonファイルをロード
            layout_info = json.load(f)
        all_lines = extract_all_lines(layout_info)
        if "BLOCKS" not in layout_info:
            continue
        img = Image.open(os.path.join(image_dir, image_file))
        for block in layout_info["BLOCKS"]:
            if(block["TYPE"] == "数式"):
                math_lines = extract_overlap_lines(all_lines, block)
                print("{} math lines.".format(len(math_lines)))
                block["LINES"] = latexocr(math_lines, img, 0.1)
    
        save_path = os.path.join(output_dir, basename_without_ext + ".json")
        with open(save_path, 'w', encoding='utf-8') as f:
            json.dump(layout_info, f, ensure_ascii=False, indent=4)

    
if __name__=="__main__":
    parser = argparse.ArgumentParser(description='Run LaTeX-OCR for Math Areas and Merge the Results to Json') 
    parser.add_argument('input', help='画像の格納されたフォルダ')
    parser.add_argument('json', help='対応するJSONファイルの格納されたフォルダ')
    parser.add_argument('output', help='結果出力先のフォルダ')

    args = parser.parse_args()

    recog_text_in_math(args.input, args.json, args.output)
