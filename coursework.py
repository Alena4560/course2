import requests
import json
import datetime

class VKPhotoDownloader:
    def __init__(self, user_id: int, token: str):
        self.user_id = user_id
        self.token = token
        self.json_data = None
        self.photo_count = 0
        self.likes_repeats = None
        self.photo_data = None
        self.photo_max_width = 0
        self.photo_max_height = 0
        self.photo_direct_url = ""
        self.photo_filename = ""

    def find_likes_repeats(self):
        likes_values = set()
        self.likes_repeats = set()
        
        for i in range(self.photo_count):
            self.photo_data = self.json_data['response']['items'][i]
            likes = self.photo_data['likes']['user_likes']
            if likes in likes_values:
                self.likes_repeats.add(likes)
            else:
                likes_values.add(likes)
        return

    def get_vk_response(self):
        host = "https://api.vk.com/method/"
        method = "photos.get"
        url = host + method
        my_params = {"owner_id": str(self.user_id), "album_id": "profile",
                    "extended": "1", "access_token": self.token, "v": "5.131"}
        response = requests.get(url, params=my_params)
        if response.status_code != 200:
            print("Запрос к Вконтакте: ОШИБКА", response.status_code)
            self.json_data = None
            return -1
        self.json_data = response.json()
        if 'error' in self.json_data:
            print("Запрос к Вконтакте: ОШИБКА",
                  self.json_data['error']['error_code'])
            self.json_data = None
            return -1

        print("Запрос к Вконтакте прошел успешно")
        self.photo_count = self.json_data['response']['count']
        print('Найдено', self.photo_count, 'фотографий')
        self.find_likes_repeats()
        return self.photo_count

    def get_max_size(self):
        height_list = [item['height'] for item in self.photo_data['sizes']]
        self.photo_max_height = max(height_list)
            
        width_list = [item['width'] for item in self.photo_data['sizes'] if
                      item['height'] == self.photo_max_height]
        self.photo_max_width = max(width_list)
        
        print('Максимальный размер:', self.photo_max_width, 'x',
              self.photo_max_height)
        return

    def get_direct_url(self):
        t_data = None
        for item in self.photo_data['sizes']:
            if item['height'] == self.photo_max_height and item['width'] == self.photo_max_width:
                t_data = item
                break
        self.photo_direct_url = t_data['url']
        print('Прямая ссылка:')
        print(self.photo_direct_url)
        return

    def get_filename(self):
        pos_vopros = self.photo_direct_url.find('?')
     
        pos_tochka = pos_vopros - 1
        while self.photo_direct_url[pos_tochka] != '.':
            pos_tochka -= 1
        
        extension = self.photo_direct_url[pos_tochka : pos_vopros]
        print("Расширение файла:", extension)
        likes = self.photo_data['likes']['user_likes']
        print('Лайков:', likes)
        self.photo_filename = str(likes)
        if likes in self.likes_repeats:
            timestamp = int(self.photo_data['date'])
            upload_date = datetime.date.fromtimestamp(timestamp).isoformat()
            self.photo_filename += '-' + upload_date
        self.photo_filename += extension
        print("Название файла при загрузке:", self.photo_filename)
        return

    def select_photo(self, index):
        if self.json_data == None:
            print("ОШИБКА: нет данных о фотографиях!")
            return "", "", 0, 0
        
        if index < 0 or index > self.photo_count:
            print("ОШИБКА: номер выходит за границы списка!")
            return "", "", 0, 0
        self.photo_data = self.json_data['response']['items'][index]
        print('id =', self.photo_data['id'])
        self.get_max_size()
        self.get_direct_url()
        self.get_filename()
               
        return self.photo_direct_url, self.photo_filename, self.photo_max_width, self.photo_max_height

class YaDiskUploader:

    def __init__(self, token: str):
        self.token = token
        self.folder_name = ""

    def create_folder(self):
        host = "https://cloud-api.yandex.net:443/"
        method = "v1/disk/resources"
        url = host + method
        time_str = datetime.datetime.now().strftime('%Y-%m-%d %H-%M')
        self.folder_name = "VK Photo Backup " + time_str
        my_headers = {"Authorization": "OAuth " + self.token}
        my_params = {"path": self.folder_name}
        response = requests.put(url, headers=my_headers, params=my_params)
        if response.status_code == 201:
            print("Создание папки на Яндекс.Диске прошло успешно")
            return True
        else:
            print("Создание папки на Яндекс.Диске: ОШИБКА", response.status_code)
            self.folder_name = ""
            return False

    def upload_photo(self, source_url: str, filename: str):
        host = "https://cloud-api.yandex.net:443/"
        method = "v1/disk/resources/upload"
        url = host + method
        my_headers = {"Authorization": "OAuth " + self.token}
        my_params = {"path": self.folder_name + '/' + filename,
                     "url": source_url}
        response = requests.post(url, headers=my_headers, params=my_params)
        if response.status_code == 202:
            print("Фотография загружена успешно")
            return True
        else:
            print("Загрузка фотографии: ОШИБКА", response.status_code)
            return False

class JSONLogger:

    def __init__(self):
        self.log = []
        self.log_name = "report.json"

    def append(self, filename: str, width: int, height: int):
        new_item = {}
        new_item['file_name'] = filename
        new_item['size'] = str(width) + 'x' + str(height)
        self.log.append(new_item)        
        return

    def save_all(self):
        f = open(self.log_name, "w")
        json.dump(self.log, f, ensure_ascii=False, indent=2)
        f.close()
        print("Сохранен отчет в файле", self.log_name)

class BackupDispatcher:

    def __init__(self):
        print("Сохранение фотографий из профиля Вконтакте на Яндекс.Диск")
        print("Введите ваш id Вконтакте (только число):")
        user_id = int(input())
        
        self.downloader = None
        self.uploader = None
        f = open("coursework.ini", "r")
        for line in f:
            key, value = line.split('=')
            if key == "vk_token":
                self.downloader = VKPhotoDownloader(user_id, value)
            if key == "ya_disk_token":
                self.uploader = YaDiskUploader(value)          
        f.close()
        self.active = True
        if self.downloader == None:
            print("ОШИБКА: не найден токен для Вконтакте!")
            self.active = False
        if self.uploader == None:
            print("ОШИБКА: не найден токен для Яндекс.Диска!")
            self.active = False
        self.logger = JSONLogger()

    def do_backup(self):
        if not self.active:
            return False
        photo_count = self.downloader.get_vk_response()
        if photo_count == -1:
            return False
        folder_result = self.uploader.create_folder()
        if not folder_result:
            return False
        result = True
        K = min(photo_count,5)
        for i in range(K):
            direct_url, photo_filename, max_width, max_height = self.downloader.select_photo(i)
            upload_result = self.uploader.upload_photo(direct_url, photo_filename)
            if upload_result:
                self.logger.append(photo_filename, max_width, max_height)
            else:
                result = False
        self.logger.save_all()
        return result

if __name__ == '__main__':
    dispatcher = BackupDispatcher()
    if not dispatcher.active:
        exit(0)
    dispatcher.do_backup()
    
