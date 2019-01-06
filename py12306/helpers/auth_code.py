import random
import time

from requests.exceptions import SSLError

from py12306.helpers.OCR import OCR
from py12306.helpers.api import API_AUTH_CODE_DOWNLOAD, API_AUTH_CODE_CHECK
from py12306.helpers.request import Request
from py12306.helpers.func import *
from py12306.log.common_log import CommonLog
from py12306.log.user_log import UserLog


class AuthCode:
    """
    验证码类
    """
    session = None
    data_path = config.RUNTIME_DIR
    retry_time = 1

    def __init__(self, session):
        self.session = session

    @classmethod
    def get_auth_code(cls, session):
        self = cls(session)
        img_path = self.download_code()
        position = OCR.get_img_position(img_path)
        answer = ','.join(map(str, position))
        if not self.check_code(answer):
            time.sleep(self.retry_time)
            return self.get_auth_code(session)
        return position

    def download_code(self):
        url = API_AUTH_CODE_DOWNLOAD.get('url').format(random=random.random())
        code_path = self.data_path + 'code.png'
        try:
            UserLog.add_quick_log(UserLog.MESSAGE_DOWNLAODING_THE_CODE).flush()
            response = self.session.save_to_file(url, code_path)  # TODO 返回错误情况
        except SSLError as e:
            UserLog.add_quick_log(
                UserLog.MESSAGE_DOWNLAOD_AUTH_CODE_FAIL.format(e, self.retry_time)).flush()
            time.sleep(self.retry_time)
            return self.download_code()
        return code_path

    def check_code(self, answer):
        """
        校验验证码
        :return:
        """
        url = API_AUTH_CODE_CHECK.get('url').format(answer=answer, random=random.random())
        response = self.session.get(url)
        result = response.json()
        if result.get('result_code') == '4':
            UserLog.add_quick_log(UserLog.MESSAGE_CODE_AUTH_SUCCESS).flush()
            return True
        else:
            UserLog.add_quick_log(
                UserLog.MESSAGE_CODE_AUTH_FAIL.format(result.get('result_message'), self.retry_time)).flush()
            self.session.cookies.clear_session_cookies()

        return False


if __name__ == '__main__':
    code_result = AuthCode.get_auth_code()
