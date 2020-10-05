import math
import os
import requests
from tqdm import tqdm


class Client:

    def __init__(self, url) -> None:
        self.url = url
        self.session = None
        self.login()
        self.pageSize = 1000

    def login(self):
        # username = input("ldap account:")
        # password = getpass.getpass()
        # username = 'jy.yang'
        # password = 'jy.1132'
        username = 'admin'
        password = 'admin123'
        method = 1
        resp = requests.post('{}/api/login'.format(self.url), json={
            "method": method,
            "username": username,
            "password": password,
        })
        resp.raise_for_status()
        body = resp.json()
        if body['code'] != 0:
            raise RuntimeError(body['message'])
        session = resp.cookies['session']
        self.session = requests.session()
        self.session.cookies['session'] = session

    def get_gts_size(self, gts_id) -> int:
        resp = self.session.get('{}/api/gts/{}'.format(self.url, gts_id))
        resp.raise_for_status()
        body = resp.json()
        if body['code'] != 0:
            raise RuntimeError(body['message'])
        return int(body['data']['count'])

    def get_gts(self, gts_id, page_num=1, page_size=1000):
        resp = self.session.get(
            '{}/api/v2/gts/{}/gt?page_num={}&page_size={}&order_by=-id'.format(self.url, gts_id, page_num, page_size))
        resp.raise_for_status()
        body = resp.json()
        if body['code'] != 0:
            raise RuntimeError(body['message'])
        return body['data']['items']

    # 添加ground truth
    def create_gt(self, gts_id, media_id, output, extra, filename=None):
        url = "{}/api/v2/gts/{}/gt".format(self.url, gts_id)
        data = {
            "input": {
                "media_id": media_id
            },
            "output": output,
            "extra": extra
        }
        if filename:
            data["input"]["filename"] = filename
        r = self.session.post(url, json=data)
        r.raise_for_status()
        return r.json()

    # 删除ground truth
    def delete_gt(self, gt_id):
        url = "{}/api/v2/gt/{}".format(self.url, gt_id)
        r = self.session.delete(url)
        r.raise_for_status()
        return r.json()

    # 登陆状态
    def login_status(self) -> dict:
        url = "{}/api/login/status".format(self.url)
        r = self.session.get(url)
        r.raise_for_status()
        res = r.json()
        if res['code'] != 0:
            raise ValueError("login status error: {}".format(res))
        return res['data']

    # 上传图片
    def upload_media(self, file_path) -> str:
        url = "{}/api/media".format(self.url)
        with open(file_path, "rb") as f:
            files = {"media": f}
            r = self.session.post(url, files=files)
            r.raise_for_status()
            res = r.json()
            if res['code'] != 0:
                raise ValueError("upload media error: {}".format(res))
            return res['data'][0]

    # 下载图片
    def download_media(self, media_id, save_path):
        url = "{}/api/media/{}".format(self.url, media_id)
        r = self.session.get(url)
        r.raise_for_status()
        with open(save_path, "wb") as f:
            f.write(r.content)

    def download_media_raw(self, media_id):
        url = "{}/api/media/{}".format(self.url, media_id)
        r = self.session.get(url)
        r.raise_for_status()
        return r.content

    # 数据集列表
    def get_gt_set(self, gts_id, page_num, page_size) -> dict:
        url = "{}/api/v2/gts/{}/gt?page_num={}&page_size={}&order_by=-id".format(self.url, gts_id, page_num, page_size)
        r = self.session.get(url)
        r.raise_for_status()
        res = r.json()
        if res['code'] != 0:
            raise ValueError("get gt set error: {}".format(res))
        return res['data']

    # 添修改ground truth
    def update_gt_extra(self, gt_id, extra):
        url = "{}/api/gt/{}/extra".format(self.url, gt_id)
        r = self.session.put(url, json={
            "Content": extra
        })
        r.raise_for_status()
        return r.json()

    # 添修改ground truth
    def update_gt_output(self, gt_id, output):
        url = "{}/api/gt/{}/output".format(self.url, gt_id)
        r = self.session.put(url, json={
            "Content": output
        })
        r.raise_for_status()
        return r.json()

    # 获取数字功能的schema
    def get_schema(self, norm_id):
        url = "{}/api/norm/{}/spec".format(self.url, norm_id)
        r = self.session.get(url)
        r.raise_for_status()
        res = r.json()
        if res['code'] != 0:
            raise ValueError("get gt set error: {}".format(res))
        return res['data']

    def import_train_data(self, data_id, input_list):
        url = "{}/api/train_data_set/{}/train_data/import".format(self.url, data_id)
        r = self.session.post(url, json={
            "input_list": input_list
        })
        r.raise_for_status()
        res = r.json()
        if res['code'] != 0:
            raise ValueError("get gt set error: {}".format(res))
        return res['data']

    def get_train_data(self, datas_id, page_num=1, page_size=1000):
        url = "{}/api/train_data_set/{}/train_data?page_size={}&page_num={}".\
            format(self.url, datas_id, page_size, page_num)
        r = self.session.get(url)
        r.raise_for_status()
        res = r.json()
        if res['code'] != 0:
            raise ValueError("get gt set error: {}".format(res))
        return res['data']

    def get_train_data_do_something(self, datas_id, do_something, start=1, end=None, **kwargs):
        pageIndex = page_start = math.ceil(start * 1.0 / self.pageSize)
        while True:
            data = self.get_train_data(datas_id, page_num=pageIndex, page_size=self.pageSize)
            items = data['items']
            page_info = data['pagination']
            num = (pageIndex-1) * self.pageSize
            if len(items) == 0:
                return
            for item in tqdm(items, total=page_info['total_count'],
                             desc=f'第{page_info["page_num"]}页,共计{page_info["total_pages"]}页'):
                num += 1
                if num < start:
                    continue
                if end and num > end:
                    return
                do_something(item, num, self, **kwargs)
            if page_info['total_pages']==page_info['page_num']:
                break
            pageIndex += 1

    def modify_train_data_annotation(self, data_id, input, output, extra):
        url = "{}/api/train_data/{}".format(self.url, data_id)
        r = self.session.patch(url, json={
            "input": input,
            "output": output,
            "extra":extra
        })
        r.raise_for_status()
        res = r.json()
        if res['code'] != 0:
            raise ValueError("get gt set error: {}".format(res))
        return res['data']
