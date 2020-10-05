import json
import os
import xml.dom.minidom

import cv2
from tqdm import tqdm

from tp.client import Client


def get_shape(points, index, type):
    return {
        "type": type,
        "name": "{}-{}".format(type, index),
        "points": points
    }


def readXML_lab(file_path):
    dom = xml.dom.minidom.parse(file_path)
    doc = dom.documentElement
    lines = doc.getElementsByTagName('Line')
    result = []
    for line in lines:
        data = {}
        points_str = line.getAttribute("Points")
        label = line.getAttribute("Label")
        point_strs = points_str.split(';')
        points=[]
        for point_str in point_strs:
            points.extend(point_str.split(','))
        for i in range(len(points)):
            points[i] = float(points[i])
        data["label"] = label
        data["ponits"] = points
        result.append(data)
    return result


def readXML_st(file_path):
    dom = xml.dom.minidom.parse(file_path)
    doc = dom.documentElement
    items = doc.getElementsByTagName('item')
    data = {}
    for item in items:
        itemID = item.getAttribute("itemID")
        if itemID == "0":
            data["date"] = item.getAttribute("value")
        elif itemID == "1":
            data["num"] = item.getAttribute("value")
        elif itemID == "2":
            data["amount"] = item.getAttribute("value")
        elif itemID == "3":
            data["amount_in_word"] = item.getAttribute("value")
        elif itemID == "4":
            data["account"] = item.getAttribute("value")
    return data


def upload_img_create_detectron(upload_dir, datas_id, tp_client:Client):
    files = [x for x in os.listdir(upload_dir) if
             x.split(".")[-1] in ['jpg', 'png', 'jpeg', 'JPG', 'PNG', 'JPEG', 'jfif']]
    media_res = []
    for file_name in tqdm(files):
        file_path = os.path.join(upload_dir, file_name)
        res = tp_client.upload_media(file_path)
        media_res.append(res)
        # break
    tp_client.import_train_data(datas_id, media_res)


def set_detectron_annotation(upload_dir, datas_id, tp_client:Client):
    def modify_detectron(item, num, client:Client, **kwargs):
        input= item["input"]["value"]
        file_name = input["filename"]
        id = item["id"]
        data_path = os.path.join(upload_dir, os.path.splitext(file_name)[0] + ".xml")
        data = readXML_lab(data_path)
        output=[]
        extra={}
        for index, item in enumerate(data):
            shape = get_shape(item["ponits"], index, "polygon")
            extra[json.dumps(["root", index])] = shape
            output.append({'label': 1})
        client.modify_train_data_annotation(id, input, output, extra)

    tp_client.get_train_data_do_something(datas_id, modify_detectron)


def set_recognition_annotation(upload_dir, datas_id, tp_client:Client):
    def modify_detectron(item, num, client:Client, **kwargs):
        input= item["input"]["value"]
        file_name = input["filename"]
        id = item["id"]
        data_path = os.path.join(upload_dir, os.path.splitext(file_name)[0] + ".xml")
        data = readXML_lab(data_path)
        output=[]
        extra={}
        for index, item in enumerate(data):
            shape = get_shape(item["ponits"], index, "polygon")
            extra[json.dumps(["root", index])] = shape
            output.append({'content': item['label']})
        client.modify_train_data_annotation(id, input, output, extra)

    tp_client.get_train_data_do_something(datas_id, modify_detectron)


def set_recognition_detectron_annotation(upload_dir, datas_id, tp_client:Client):
    def modify_detectron(item, num, client:Client, **kwargs):
        input= item["input"]["value"]
        file_name = input["filename"]
        id = item["id"]
        data_path = os.path.join(upload_dir, os.path.splitext(file_name)[0] + ".xml")
        data = readXML_lab(data_path)
        output=[]
        extra={}
        for index, item in enumerate(data):
            shape = get_shape(item["ponits"], index, "polygon")
            extra[json.dumps(["root", index])] = shape
            output.append({'content': item['label'], "label": 1})
        client.modify_train_data_annotation(id, input, output, extra)

    tp_client.get_train_data_do_something(datas_id, modify_detectron)


def upload_img_create_gt(upload_dir, gts_id, tp_client:Client):
    files = [x for x in os.listdir(upload_dir) if
             x.split(".")[-1] in ['jpg', 'png', 'jpeg', 'JPG', 'PNG', 'JPEG', 'jfif']]
    for file_name in tqdm(files):
        file_path = os.path.join(upload_dir, file_name)
        data_path = os.path.join(upload_dir, os.path.splitext(file_name)[0]+"_st.xml")
        res = tp_client.upload_media(file_path)
        output = readXML_st(data_path)
        tp_client.create_gt(gts_id, res["media_id"], output, {}, res["filename"])
        # break


def split_dp_data(folder_path):
    '''
    切割图片， 将小图从1开始编码保存在folder_path目录下split文件夹下，图片对应的值保存在split文件夹下的values.txt中，第一行对应编号为1的图片
    :param folder_path: 保存dp图片和gt的文件夹
    :return:
    '''
    files = list(map(lambda f: os.path.splitext(f)[0], filter(lambda x: x.endswith('.json'), os.listdir(folder_path))))
    save_path = os.path.join(folder_path, 'split')
    if not os.path.exists(save_path):
        os.makedirs(save_path)
    i = 0

    def convert_to_int(text):
        num = int(text)
        if num < 0:
            num = 0
        return num
    with open(os.path.join(save_path, 'values.txt'), 'w', encoding='utf8') as val_f:
        for file_name in tqdm(files):
            data = readXML_lab(os.path.join(folder_path, file_name + '.xml'))
            img_filename = os.path.join(folder_path, file_name + '.jpg')
            img = cv2.imread(img_filename)
            for item in data:
                val_f.write(f'{item["label"]}\n')
                # cv2.imwrite(os.path.join(save_path, str(i) + '.jpg'), cropped)


if __name__ == "__main__":
    tp_client = Client("http://tp.tg4.tianrang-inc.com")
    root_dir = r"D:\poc\苏州\trainData"
    gts_id = 1
    datas_id= 5
    # upload_img_create_gt(root_dir, gts_id, tp_client)
    # upload_img(tp_client)
    #
    # data = readXML_lab(r"D:\poc\苏州\trainData\OCR_0000.xml")
    # print(data)
    upload_img_create_detectron(root_dir, datas_id, tp_client)
    # set_detectron_annotation(root_dir, datas_id, tp_client)
    # set_recognition_annotation(root_dir, datas_id, tp_client)
    set_recognition_detectron_annotation(root_dir, datas_id, tp_client)