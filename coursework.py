import requests
import json
import datetime

def get_vk_id():
    print("Введите ваш id Вконтакте (только число):")
    return int(input())

def get_disk_token():
    print("Введите токен с Полигона Яндекс.Диска:")
    return input()

def get_vk_response(vk_id):
    token = ""
    host = "https://api.vk.com/method/"
    method = "photos.get"
    url = host + method
    my_params = {"owner_id": str(vk_id), "album_id": "profile",
                "extended": "1", "access_token": token, "v": "5.131"}
    response = requests.get(url, params=my_params)
    if response.status_code != 200:
        print("Запрос к Вконтакте: ОШИБКА", response.status_code)
        return None
    result = response.json()
    if 'error' in result:
        print("Запрос к Вконтакте: ОШИБКА", result['error']['error_code'])
        return None
    print("Запрос к Вконтакте прошел успешно")
    return result

def create_folder(token):
    host = "https://cloud-api.yandex.net:443/"
    method = "v1/disk/resources"
    url = host + method
    time_str = datetime.datetime.now().strftime('%Y-%m-%d %H-%M')
    folder_name = "VK Photo Backup " + time_str
    my_headers = {"Authorization": "OAuth " + token}
    my_params = {"path": folder_name}
    response = requests.put(url, headers=my_headers, params=my_params)
    if response.status_code == 201:
        print("Создание папки на Яндекс.Диске прошло успешно")
        return folder_name
    else:
        print("Создание папки на Яндекс.Диске: ОШИБКА", response.status_code)
        return None

def upload_photo(direct_url, file_name, folder_name, token):
    host = "https://cloud-api.yandex.net:443/"
    method = "v1/disk/resources/upload"
    url = host + method
    my_headers = {"Authorization": "OAuth " + token}
    my_params = {"path": folder_name + '/' + file_name, "url": direct_url}
    response = requests.post(url, headers=my_headers, params=my_params)
    if response.status_code == 202:
        print("Фотография загружена успешно")
        return True
    else:
        print("Загрузка фотографии: ОШИБКА", response.status_code)
        return False

def get_filename(direct_url, likes, timestamp):
    pos_vopros = direct_url.find('?')
 
    pos_tochka = pos_vopros - 1
    while direct_url[pos_tochka] != '.':
        pos_tochka -= 1
    
    extension = direct_url[pos_tochka : pos_vopros]
    print("Расширение файла:", extension)
    result = str(likes)
    if timestamp != None:
        upload_date = datetime.date.fromtimestamp(timestamp).isoformat()
        result += '-' + upload_date
    result += extension
    print("Название файла при загрузке:", result)
    return result

def get_max_size(photo_data):
    height_list = [item['height'] for item in photo_data['sizes']]
    max_height = max(height_list)
        
    width_list = [item['width'] for item in photo_data['sizes'] if item['height'] == max_height]
    max_width = max(width_list)
    
    print('Максимальный размер:', max_width, 'x', max_height)
    return max_width, max_height

def get_direct_url(photo_data, max_width, max_height):
    t_data = None
    for item in photo_data['sizes']:
        if item['height'] == max_height and item['width'] == max_width:
            t_data = item
            break
    result = t_data['url']
    print('Прямая ссылка:')
    print(result)
    return result

def append_json_report(report, filename, max_width, max_height):
    new_item = dict()
    new_item['file_name'] = filename
    new_item['size'] = str(max_width) + 'x' + str(max_height)
    report.append(new_item)

def save_json_report(report):
    f = open("report.json", "w")
    json.dump(report, f, ensure_ascii=False, indent=2)
    f.close()
    print("Сохранен отчет в файле report.json")

def process_photo(photo_data, repeated_likes, folder_name, token, report):
    print('id =', photo_data['id'])
    max_width, max_height = get_max_size(photo_data)
    direct_url = get_direct_url(photo_data, max_width, max_height)
    likes = photo_data['likes']['user_likes']
    print('Лайков:', likes)
    if likes in repeated_likes:
        timestamp = int(photo_data['date'])
    else:
        timestamp = None
    filename = get_filename(direct_url, likes, timestamp)
    upload_result = upload_photo(direct_url, filename, folder_name, token)
    if upload_result:
        append_json_report(report, filename, max_width, max_height)
        return True
    else:
        return False

def find_repeated_likes(json_data):
    likes_values = [item['likes']['user_likes'] for
                    item in json_data['response']['items'][:5]]
    
    result = {n for n in likes_values if likes_values.count(n) >= 2} 
    return result

def process_all_photo(json_data, token):
    count = json_data['response']['count']
    print('Найдено', count, 'фотографий')
    K = min(5, count)
    folder_name = create_folder(token)
    if folder_name == None:
        return False
    repeated_likes = find_repeated_likes(json_data)
    json_report = list()
    for i in range(K):
        photo_data = json_data['response']['items'][i]
        photo_result = process_photo(photo_data, repeated_likes, folder_name,
                                     token, json_report)
        if not photo_result:
            print("Процесс прерван: ошибка при обработке фотографии")
            return False
    save_json_report(json_report)   
    return True

print("Сохранение фотографий из профиля Вконтакте на Яндекс.Диск")
vk_id = get_vk_id()
disk_token = get_disk_token()
json_data = get_vk_response(vk_id)
process_all_photo(json_data, disk_token)