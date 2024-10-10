import os
import subprocess
import json
import argparse 
from PIL import Image
from draw_result import draw_shapes_from_xml
from read_ndlocr_xml import parse_ocr_result, convert_format
from main import infer
import click
from click.testing import CliRunner

def run_infer(proc_folder, result_path, input_structure, proc_range):
    runner = CliRunner()
    result = runner.invoke(
        infer, 
        [proc_folder, result_path, '-s', input_structure, '-x', '-p', proc_range]
    )
    if result.exit_code != 0:
        print(result.output)
        raise result.exception


def convert_images(input_folder, output_folder, save_json):
    # 画像ファイル名一覧を取得
    image_files = [f for f in os.listdir(input_folder) if f.lower().endswith(('.png', '.jpeg', '.jpg', '.bmp', '.gif'))]
    
    # NDL OCRの結果を保存するフォルダ
    proc_folder = os.path.join(output_folder, "tmpdir")
    if(not os.path.exists(proc_folder)):
        os.mkdir(proc_folder)

    # 連番ファイル名とオリジナルファイル名の関係を保存
    filename_mapping = {}
    
    # 画像をjpgに変換して保存
    image_dir = os.path.join(proc_folder, 'img')
    if(not os.path.exists(image_dir)):
        os.mkdir(image_dir)
    for i, image_file in enumerate(image_files):
        original_path = os.path.join(input_folder, image_file)
        new_filename = f"R{i+1:07d}.jpg"
        new_path = os.path.join(image_dir, new_filename)
        
        with Image.open(original_path) as img:
            img.convert('RGB').save(new_path, 'JPEG')
            print("convert {} to {}".format(original_path, new_path))
        
        filename_mapping[new_filename] = image_file
    
    # 連番ファイル名とオリジナルファイル名の関係を保存
    with open(os.path.join(proc_folder, 'filename_mapping.json'), 'w') as f:
        json.dump(filename_mapping, f)
    
    # NDL OCRを起動
    result_path = os.path.join(proc_folder, 'result')
    try:
        run_infer(proc_folder, result_path, input_structure='s', proc_range='2..3')
    except Exception as e:
        print(f"Exception occurred: {e}")
    #proc_folder_abs = os.path.abspath(proc_folder)     # 絶対パスに変換
    #subprocess.run(['./run_ndlocr.sh', proc_folder_abs])

    # 結果の描画
    xml_path = os.path.join(result_path, 'tmpdir/xml/tmpdir.sorted.xml')
    preimg_dir = os.path.join(result_path, 'tmpdir/pred_img')
    draw_path = os.path.join(proc_folder, 'draw')
    if(not os.path.exists(draw_path)):
        os.mkdir(draw_path)
    draw_shapes_from_xml(xml_path, preimg_dir, draw_path)

    # 描画結果のファイル名を連番から元のファイル名に戻す
    output_draw_folder = os.path.join(output_folder, 'draw')
    if(not os.path.exists(output_draw_folder)):
        os.mkdir(output_draw_folder)
    for new_filename, original_filename in filename_mapping.items():
        new_path = os.path.join(draw_path, new_filename)
        original_path = os.path.join(output_draw_folder, os.path.splitext(original_filename)[0] + '.jpg')        
        if os.path.exists(new_path):
            os.rename(new_path, original_path)
    os.rmdir(draw_path)
    
    # XMLファイルを読み込み
    if(save_json):
        json_folder = os.path.join(output_folder, 'json')
        if(not os.path.exists(json_folder)):
            os.mkdir(json_folder)
        ocr_page_results = parse_ocr_result(xml_path)
        ocr_page_results = convert_format(ocr_page_results)

        for image_name, contents in ocr_page_results.items():
            original_name = filename_mapping.get(image_name)
            if original_name:
                json_path = os.path.join(json_folder, f"{os.path.splitext(original_name)[0]}.json")
                with open(json_path, 'w', encoding='utf-8') as f:
                    json.dump(contents, f, ensure_ascii=False, indent=4)
    

if __name__=="__main__":
    parser = argparse.ArgumentParser(description='NDL OCR Wrapper') 

    parser.add_argument('input', help='画像の格納されたフォルダ')
    parser.add_argument('output', help='結果出力先のフォルダ')
    parser.add_argument('-j', '--json', help='結果をXMLからJSONへ変換', action='store_true', default=False)

    args = parser.parse_args()

    # 使用例
    convert_images(args.input, args.output, args.json)
