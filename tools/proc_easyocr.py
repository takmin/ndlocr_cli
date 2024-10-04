import argparse 
import easyocr
import os
import cv2
import json
from read_ndlocr_xml import check_line_overlap


reader = easyocr.Reader(['ja','en']) # this needs to run only once to load the model into memory


def convert_line_easy2ndl(line, bx, by):
    points = line[0]

    # 各座標のxとyの最小値と最大値を求める
    min_x = min(point[0] for point in points)
    max_x = max(point[0] for point in points)
    min_y = min(point[1] for point in points)
    max_y = max(point[1] for point in points)

    x = bx + min_x
    y = by + min_y
    width = max_x - min_x
    height = max_y - min_y
    string = line[1]
    conf = line[2]
    return {
        'TYPE': "EasyOCR",
        'X': int(x),
        'Y': int(y),
        'WIDTH': int(width),
        'HEIGHT': int(height),
        'CONF': float(conf),
        'STRING': string,
        'ORDER': 0,
        'TITLE': "FALSE",
        'AUTHOR': "FALSE"
    }


def extract_lines_easyocr(block, img, margin, threshold=0.0):
    # マージンを取って画像を切り抜き
    W = block["WIDTH"]
    H = block["HEIGHT"]
    margin_w = W * margin
    margin_h = H * margin
    bx = max(int(block["X"] - margin_w / 2), 0)
    by = max(int(block["Y"] - margin_h / 2), 0)
    ex = min(int(bx + W + margin_w), img.shape[1])
    ey = min(int(by + H + margin_h), img.shape[0])
    img_roi = img[by:ey, bx:ex]

    # EasyOCRをかける
    result = reader.readtext(img_roi)
    order = 1
    lines = []
    for line in result:
        ndl_line = convert_line_easy2ndl(line, bx, by)
        if (check_line_overlap(ndl_line, block) > 0.5 and ndl_line["CONF"] > threshold):
            ndl_line["ORDER"] = order
            order += 1
            lines.append(ndl_line)
    return lines


def recog_text_in_table_and_figure(image_dir, json_dir, output_dir, threshold=0.0):
    """
    1. 画像ファイルをロード
    2. 対応するjsonファイルをロード
    3. jsonから表組領域または図版領域を抽出
    4. 領域にマージンを取った領域で画像を切り取り
    5. 切り取った画像に対してEasyOCRをかける
    6. 認識結果をjsonへ再格納
    """
    # 画像ファイル名一覧を取得
    image_files = [f for f in os.listdir(image_dir) if f.lower().endswith(('.png', '.jpeg', '.bmp', '.gif'))]

    if(not os.path.exists(output_dir)):
        os.mkdir(output_dir)
    
    for image_file in image_files:
        print("processing {}".format(image_file))
        img = cv2.imread(os.path.join(image_dir, image_file))
        basename_without_ext = os.path.splitext(os.path.basename(image_file))[0]

        # jsonファイル名は＜画像ファイル名＞.json
        json_file = os.path.join(json_dir, basename_without_ext + ".json")
        with open(json_file) as f:
            # jsonファイルをロード
            layout_info = json.load(f)
        if "BLOCKS" not in layout_info:
            continue
        for block in layout_info["BLOCKS"]:
            if(block["TYPE"] == "図版" or block["TYPE"] == "表組"):
                block["LINES"] = extract_lines_easyocr(block, img, 0.1, threshold)
    
        save_path = os.path.join(output_dir, basename_without_ext + ".json")
        with open(save_path, 'w', encoding='utf-8') as f:
            json.dump(layout_info, f, ensure_ascii=False, indent=4)

    
if __name__=="__main__":
    parser = argparse.ArgumentParser(description='Run EasyOCR for Figure and Table Areas and Merge the Results to Json') 
    parser.add_argument('input', help='画像の格納されたフォルダ')
    parser.add_argument('json', help='対応するJSONファイルの格納されたフォルダ')
    parser.add_argument('output', help='結果出力先のフォルダ')
    parser.add_argument('--threshold', default=0.0, help='検出閾値')

    args = parser.parse_args()

    recog_text_in_table_and_figure(args.input, args.json, args.output, args.threshold)
