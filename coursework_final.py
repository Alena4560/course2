import requests
import json
import datetime

# получение от пользователя id Вконтакте
def get_vk_id():
    print("Введите ваш id Вконтакте (только число):")
    return int(input())

# получение от пользователя токена Яндекс.Диска
def get_disk_token():
    print("Введите токен с Полигона Яндекс.Диска:")
    return input()
    
# получение от Вконтакте ответа на запрос по фотографиям
# в случае успеха функция возвращает ответ на запрос в формате json
# в случае ошибок функция возвращает None
# параметр - id пользователя Вконтакте
def get_vk_response(vk_id):
    
    # токен заранее получен через работу с сайтом вручную
    token = "vk1.a.8tGcMwjsTM1sWz62EVvV6FLsTyUBAYvIpebfb75k-i4iuE6uLqvlG2NNlj3dqHFarLzVwjrXpftUs2P6Exy5nEkHIQO53LSJ4W37z_NeLm06CRPkVXqDv4uFCGqmIcQHD1YQgkhoD51JGJzdHCSwuD-MA34ijju3pae9yax0nzcsxpKN1Iqmb4JIfxq-_yQb"
    
    # формирование url для запроса
    host = "https://api.vk.com/method/"
    method = "photos.get"
    url = host + method
    
    # формирование параметров запроса
    my_params = {"owner_id": str(vk_id), "album_id": "profile",
                "extended": "1", "access_token": token, "v": "5.131"}
    
    # сам http-запрос
    response = requests.get(url, params=my_params)
    
    # разбор ошибок при ответе на запрос
    if response.status_code != 200:
        print("Запрос к Вконтакте: ОШИБКА", response.status_code)
        return None
    
    # из ответа на запрос извлекается результат - данные в формате json
    result = response.json()
    
    # разбор ошибок на новом этапе
    if 'error' in result:
        print("Запрос к Вконтакте: ОШИБКА", result['error']['error_code'])
        return None
    
    # возвращение результата при отсутствии ошибок
    print("Запрос к Вконтакте прошел успешно")
    return result
    
# создание новой папки на Яндекс.Диске
# в случае успеха функция возвращает название папки (оно индивидуально и
# зависит от текущего времени), в случае ошибок возвращает None
# параметр - токен от Яндекс.Диска
def create_folder(token):

    # формирование url для запроса
    host = "https://cloud-api.yandex.net:443/"
    method = "v1/disk/resources"
    url = host + method
    
    # получение текущего времени и создание названия папки
    time_str = datetime.datetime.now().strftime('%Y-%m-%d %H-%M')
    folder_name = "VK Photo Backup " + time_str
    
    # формирование заголовков и параметров запроса
    my_headers = {"Authorization": "OAuth " + token}
    my_params = {"path": folder_name}
    
    # сам http-запрос
    response = requests.put(url, headers=my_headers, params=my_params)

    # разбор ошибок и возвращение результата
    if response.status_code == 201:
        print("Создание папки на Яндекс.Диске прошло успешно")
        return folder_name
    else:
        print("Создание папки на Яндекс.Диске: ОШИБКА", response.status_code)
        return None

# загрузка одной фотографии на Яндекс.Диск по прямой ссылке
# в случае успеха возвращает True, в случае ошибок возвращает False
# параметры: direct_url - прямая ссылка на загружаемое фото
# file_name - имя файла, под которым фото будет записано на Яндекс.Диск
# folder_name - имя папки на Яндекс.Диске, куда будет загружено фото
# token - токен от Яндекс.Диска
def upload_photo(direct_url, file_name, folder_name, token):
    
    # формирование url для запроса
    host = "https://cloud-api.yandex.net:443/"
    method = "v1/disk/resources/upload"
    url = host + method

    # формирование заголовков и параметров запроса
    my_headers = {"Authorization": "OAuth " + token}
    my_params = {"path": folder_name + '/' + file_name, "url": direct_url}
       
    # сам http-запрос
    response = requests.post(url, headers=my_headers, params=my_params)
    
    # разбор ошибок и возвращение результата
    if response.status_code == 202:
        print("Фотография загружена успешно")
        return True
    else:
        print("Загрузка фотографии: ОШИБКА", response.status_code)
        return False

# получение имени файла для загрузки фотографии на Яндекс.Диск
# функция возвращает имя файла
# параметры: direct_url - прямая ссылка на фото
# likes - количество лайков
# timestamp - момент загрузки в формате timestamp,
# если дату нужно добавить к названию (если нет, то timestamp=None)
def get_filename(direct_url, likes, timestamp):
    
    # из прямой ссылки извлекаем расширение файла
    # для этого нужна позиция знака ? в тексте ссылки
    # и позиция ближайшей точки перед знаком ?
    pos_vopros = direct_url.find('?')
 
    pos_tochka = pos_vopros - 1
       while direct_url[pos_tochka] != '.':
        pos_tochka -= 1
    
    extension = direct_url[pos_tochka : pos_vopros]
    print("Расширение файла:", extension)
    
    # начинаем создавать результат - будущее имя файла
    result = str(likes)
    
    # обраотка случая, когда нужно добавить к названию дату загрузки
    if timestamp != None:
        upload_date = datetime.date.fromtimestamp(timestamp).isoformat()
        result += '-' + upload_date
        
    # к имени файла добавляем расширение и возвращаем результат
    result += file_extension
    print("Название файла при загрузке:", result)
    return result

# получение максимальных размеров фотографии
# функция возвращает 2 числа: ширину и высоту (макс. ширина при макс. высоте)
# параметр photo_data - данные о фотографии в формате json
def get_max_size(photo_data):
    
    # выбираем в списке разновидностей максимальный размер
    height_list = [item['height'] for item in photo_data['sizes']]
    max_height = max(height_list)
        
    width_list = [item['width'] for item in photo_data['sizes'] if item['height'] == max_height]
    max_width = max(width_list)
    
    print('Максимальный размер:', max_width, 'x', max_height)
    return max_width, max_height


# получение прямой ссылки на фото в максимальном размере
# функция возвращаем ссылку как строку
# параметры: photo_data - данные о фотографии в формате json
# max_width и max_height - максимальные размеры
def get_direct_url(photo_data, max_width, max_height):

    # перебираем данные о фотографии в разных размерах и выбираем те,
    # где размер совпадает с максимальным
    t_data = None
    for item in photo_data['sizes']:
        if item['height'] == max_height and item['width'] == max_width:
            t_data = item
            break
    
    # из найденных данных извлекаем url и возвращаем как результат
    result = t_data['url']
    print('Прямая ссылка:')
    print(result)
    return result

# дополнить отчет в формате json сведениями об одном фото
# параметры: report - ссылка на отчет
# filename - имя файля
# max_width и max_height - макс. размеры фотографии
def append_json_report(report, filename, max_width, max_height):
    new_item = dict()
    new_item['file_name'] = filename
    new_item['size'] = str(max_width) + 'x' + str(max_height)
    report.append(new_item)
    
# полный комплекс обработки одного фото
# функция возвращает True если всё полуячилось и False, если были ошибки
# параметры: photo_data - данные о фотографии в формате json
# repeated_likes - множество значений лайков, которые повторяются
# folder_name - название папки на Яндекс.Диске, куда надо загружать
# token - токен от Яндекс.Диска
# report - ссылка на отчет в формате json
def process_photo(photo_data, repeated_likes, folder_name, token, report):
    print(': id =', photo_data['id'])
    
    # находим максимальные размеры   
    max_width, max_height = get_max_size(photo_data)

    # получаем прямую ссылку на фото максимального размера
    direct_url = get_direct_url(photo_data, max_width, max_height)
    
    # находим кол-во лайков
    likes = photo_data['likes']['user_likes']
    print('Лайков:', likes)
    
    # если это кол-во среди повторяющихся значений,
    # то к названию надо добавить дату загрузки
    if likes in repeated_likes:
        timestamp = int(photo_data['date'])
    else:
        timestamp = None
    
    # получаем имя файла
    filename = get_filename(direct_url, likes, timestamp)
    
    # завершаем формирование параметров и посылаем запрос на загрузку фото    
    upload_result = upload_photo(direct_url, filename, folder_name, token)
    
    # после удачной загрузки создаем запись для отчета в json
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
   
# 
def process_all_photo(json_data, token):
    
    # извлекаем число найденных фотографий
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
        process_photo(photo_data, repeated_likes, folder_name, token, json_report)
        
    f = open("report.json", "w")
    json.dump(json_report, f, ensure_ascii=False, indent=2)
    f.close()
    print("Сохранен отчет в файле report.json")
    
   
# Основная часть программы
print("Сохранение фотографий из профиля Вконтакте на Яндекс.Диск")

vk_id = get_vk_id()

disk_token = get_disk_token()

json_data = get_vk_response(vk_id)

process_all_photo(json_data, disk_token)