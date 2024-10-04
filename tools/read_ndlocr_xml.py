import xml.etree.ElementTree as ET
import argparse 
import json


def parse_line(line):
    return {
        'TYPE': line.get('TYPE'),
        'X': int(line.get('X')),
        'Y': int(line.get('Y')),
        'WIDTH': int(line.get('WIDTH')),
        'HEIGHT': int(line.get('HEIGHT')),
        'CONF': float(line.get('CONF')) if line.get('CONF') is not None else None,
        'STRING': line.get('STRING'),
        'ORDER': int(line.get('ORDER')),
        'TITLE': line.get('TITLE'),
        'AUTHOR': line.get('AUTHOR')
    }

def parse_ocr_result(xml_path):  
    # XMLファイルを読み込み
    tree = ET.parse(xml_path)
    root = tree.getroot()

    page_list = []
    
    # XMLをページごとに読み込み、jsonに変換して保存
    for page in root.findall('PAGE'):
        page_dict = {
            'IMAGENAME': page.get('IMAGENAME'),
            'WIDTH': int(page.get('WIDTH')),
            'HEIGHT': int(page.get('HEIGHT')),
            'TEXTBLOCKS': [],
            'LINES': [],
            'BLOCKS': []
        }
        for textblock in page.findall('TEXTBLOCK'):
            textblock_dict = {
                'CONF': textblock.get('CONF'),
                'LINES': []
            }
            for line in textblock.findall('LINE'):
                textblock_dict['LINES'].append(parse_line(line))
            
            for shape in textblock.findall('SHAPE'):
                input_string = shape.find('POLYGON').get('POINTS')
                shape_dict = {
                    'POLYGON': list(map(int, input_string.split(',')))
                }
                textblock_dict['SHAPE'] = shape_dict
            
            page_dict['TEXTBLOCKS'].append(textblock_dict)
        
        for line in page.findall('LINE'):
            page_dict['LINES'].append(parse_line(line))
        
        for block in page.findall('BLOCK'):
            block_dict = {
                'TYPE': block.get('TYPE'),
                'X': int(block.get('X')),
                'Y': int(block.get('Y')),
                'WIDTH': int(block.get('WIDTH')),
                'HEIGHT': int(block.get('HEIGHT')),
                'CONF': float(block.get('CONF')),
                'STRING': block.get('STRING')
            }
            page_dict['BLOCKS'].append(block_dict)
        
        page_list.append(page_dict)    
    return page_list


def bounding_box(polygon:list):
    # x座標とy座標をそれぞれ抽出
    x_coords = polygon[0::2]
    y_coords = polygon[1::2]

    # 最小値と最大値を求める
    min_x = min(x_coords)
    max_x = max(x_coords)
    min_y = min(y_coords)
    max_y = max(y_coords)
    return [min_x, min_y, max_x - min_x, max_y - min_y]


def convert_text_blocks(text_block:dict):
    converted_block = {}
    text_box = bounding_box(text_block["SHAPE"]["POLYGON"])
    converted_block["TYPE"] = "テキスト"
    converted_block["X"] = text_box[0]
    converted_block["Y"] = text_box[1]
    converted_block["WIDTH"] = text_box[2]
    converted_block["HEIGHT"] = text_box[3]
    converted_block["CONF"] = text_block["CONF"]
    converted_block["LINES"] = text_block["LINES"]
    return converted_block


def extract_box_corners(block:dict):
    return [
        block["X"],
        block["Y"],
        block["WIDTH"] + block["X"],
        block["HEIGHT"] + block["Y"]
    ]


def check_line_overlap(line:dict, block:dict):
    x1, y1, x2, y2 = extract_box_corners(line)
    x3, y3, x4, y4 = extract_box_corners(block)

    # オーバーラップする領域の左下と右上の座標を計算
    overlap_x1 = max(x1, x3)
    overlap_y1 = max(y1, y3)
    overlap_x2 = min(x2, x4)
    overlap_y2 = min(y2, y4)

    # オーバーラップする領域の幅と高さを計算
    overlap_width = max(0, overlap_x2 - overlap_x1)
    overlap_height = max(0, overlap_y2 - overlap_y1)

    # オーバーラップする面積を計算
    overlap_area = overlap_width * overlap_height

    # オーバーラップ率
    return overlap_area / (line["WIDTH"] * line["HEIGHT"])


def convert_format(ndl_format:list):
    """
    NDL OCRのXMLをそのまま読み込んだdictionary形式を、VLMトレーニング用フォーマットへ変更
    """
    converted_format = {}
    for ocr_page in ndl_format:
        image_name = ocr_page["IMAGENAME"]
        page_contents = {
            "WIDTH": ocr_page["WIDTH"],
            "HEIGHT": ocr_page["HEIGHT"],
            "LINES": [],
            "BLOCKS": []
        }

        text_blocks = []
        blocks = []
        if("TEXTBLOCKS" in ocr_page):
            text_blocks = [convert_text_blocks(text_block) for text_block in ocr_page["TEXTBLOCKS"]]
        if("BLOCKS" in ocr_page):
            blocks = ocr_page["BLOCKS"]

        if("LINES" in ocr_page):
            # Lineが0.5以上オーバーラップするBLOCKへ追加
            lines = []
            for line in ocr_page["LINES"]:
                overlap = False
                for block in blocks:
                    overlap = check_line_overlap(line, block)
                    if(overlap > 0.5):
                        overlap = True
                        if("LINES" in block):
                            block["LINES"].append(line)
                        else:
                            block["LINES"] = [line]
                        break
                if(overlap == False):
                    lines.append(line)
            page_contents["LINES"] = lines
        page_contents["BLOCKS"] = text_blocks + blocks
        converted_format[image_name] = page_contents
    return converted_format


if __name__=="__main__":
    parser = argparse.ArgumentParser(description='NDL OCR XML Reader') 

    parser.add_argument('input', help='入力XMLファイル')
    parser.add_argument('output', help='出力JSONファイル')
    parser.add_argument('--convert', default=False, help='フォーマットをVLMトレーニング用に変換')
    args = parser.parse_args()
    ocr_result = parse_ocr_result(args.input)
    if(args.convert):
        ocr_result = convert_format(ocr_result)

    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(ocr_result, f, ensure_ascii=False, indent=4)
