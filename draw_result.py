import os
import xml.etree.ElementTree as ET
import argparse 
from PIL import Image, ImageDraw, ImageFont


def draw_line(draw, line, font):
    x = int(line.get('X'))
    y = int(line.get('Y'))
    width = int(line.get('WIDTH'))
    height = int(line.get('HEIGHT'))
    line_type = line.get('TYPE')
    
    if line_type == '本文':
        color = 'red'
    else:
        color = 'orange'
        draw.text((x, y), line_type, fill=color, font=font)
    
    draw.rectangle([x, y, x + width, y + height], outline=color)

def draw_shapes_from_xml(xml_file, img_dir, output_dir):
    # XMLファイルをパース
    tree = ET.parse(xml_file)
    root = tree.getroot()
    
    # 日本語フォントを指定
    font_path = './fonts/ipaexg.ttf'
    font = ImageFont.truetype(font_path, 20)

    for page in root.findall('PAGE'):
        image_name = page.get('IMAGENAME')
        image_path = os.path.join(img_dir, image_name)
        
        # 画像を開く
        image = Image.open(image_path)
        draw = ImageDraw.Draw(image)
        
        # <LINE>タグの処理
        for line in page.findall('LINE'):
            draw_line(draw, line, font) 

        # <BLOCK>タグの処理
        for block in page.findall('BLOCK'):
            x = int(block.get('X'))
            y = int(block.get('Y'))
            width = int(block.get('WIDTH'))
            height = int(block.get('HEIGHT'))
            block_type = block.get('TYPE')
            
            color = 'green'
            draw.rectangle([x, y, x + width, y + height], outline=color)
            draw.text((x, y), block_type, fill=color, font=font)
        
        # <TEXTBLOCK>タグの処理
        for textblock in page.findall('TEXTBLOCK'):
            for line in textblock.findall('LINE'):
                draw_line(draw, line, font)

            for shape in textblock.findall('SHAPE'):
                for polygon in shape.findall('POLYGON'):
                    points = polygon.get('POINTS').split(',')
                    points = [(int(points[i]), int(points[i+1])) for i in range(0, len(points), 2)]
                    
                    color = 'blue'
                    draw.polygon(points, outline=color)
        
        # 画像を保存
        output_path = os.path.join(output_dir, image_name)
        image.save(output_path)


if __name__=="__main__":
    parser = argparse.ArgumentParser(description='NDL OCRの結果描画プログラム') 
    parser.add_argument('input', help='NDL OCRの出力先ディレクトリ')
    parser.add_argument('output', help='描画画像出力先ディレクトリ')
    args = parser.parse_args()
    draw_shapes_from_xml(args.input, args.output)
    #draw_shapes_from_xml('./result/', './draw2')
