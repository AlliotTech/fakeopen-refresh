import yaml
import requests
import base64
from pandora.openai.auth import Auth0

URL="https://ai.fakeopen.com"

class TokenManager:
    """
    TokenManager类用于管理用户的token，包括获取token、注册token、更新token池等功能。

    Args:
        config_file (str): 配置文件路径。
        pool_token (str, optional): token池中的token。默认为None。

    Attributes:
        accounts (list): 包含用户名和密码的字典列表。
        share_tokens (list): 已注册的token列表。
        pool_token (str): token池中的token。

    Methods:
        get_token(username, password): 获取用户的token。
        register_token(username, access_token): 注册用户的token。
        update_pool(): 更新token池中的token。
        run(): 运行TokenManager实例，获取并更新token池中的token。

    """
    def __init__(self, config_file, pool_token=None):
        with open(config_file, 'r') as f:
            self.accounts = yaml.safe_load(f)

        self.share_tokens = []
        self.pool_token = pool_token

    def get_token(self, username, password):
        """
        获取用户的token。

        Args:
            username (str): 用户名。
            password (str): 密码。

        Returns:
            str: 用户的token。

        """
        proxy = ''
        try:
            token = Auth0(username, password, proxy).auth(False)
            print(f'Login success: {username}')
            print(token)
        except Exception as e:
            err_str = str(e).replace('\n', '').replace('\r', '').strip()
            print(f'Login failed: {username}, {err_str}')
            token = err_str
        return token


    def register_token(self, username, access_token):
        """
        注册用户的token。

        Args:
            username (str): 用户名。
            access_token (str): 用户的token。

        Returns:
            str: 注册成功后返回的token_key。

        """
        unique_name = base64.b64encode(username.encode()).decode()
        data =f'unique_name={unique_name}&access_token={access_token}&expires_in=0&site_limit='
        headers = {'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'}

        response = requests.post(f'{URL}/token/register',headers=headers, data=data)
        # print(response.text)
        response.raise_for_status()

        return response.json()['token_key']

    def update_pool(self):
        """
        更新token池中的token。

        """
        share_tokens_str = '%0D%0A'.join(self.share_tokens)
        data = f'share_tokens={share_tokens_str}'
        headers = {'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'}
        if self.pool_token is not None:
            data += f'&pool_token={self.pool_token}'
            print('更新:', self.pool_token)
        print(f'Request content: {data}')

        response = requests.post(f'{URL}/pool/update', headers=headers, data=data)
        response.raise_for_status()
        print(response.text)
        self.pool_token = response.json()['pool_token']
    def run(self):
        """
        运行TokenManager实例，获取并更新token池中的token。

        Returns:
            str: 更新后的token池中的token。

        """
        for account in self.accounts:
            username = account['username']
            password = account['password']
            access_token = self.get_token(username, password)
            share_token = self.register_token(username, access_token)
            self.share_tokens.append(share_token)
        self.update_pool()
        return self.pool_token

if __name__ == '__main__':
    # 如果不传入pool_token，则为创建新的pool_token，否则为更新现有的pool_token 
    manager = TokenManager('config.yaml')
    # manager = TokenManager('config.yaml', pool_token='pk-xxx')

    pool_token = manager.run()
    print(pool_token)

