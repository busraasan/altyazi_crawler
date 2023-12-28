from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import os
import glob
import pickle

home = os.path.expanduser('~')
path = os.path.join(home, 'Downloads')
path_a = path + "/*" # * means (match all), if specific format required then *.csv This will get all the files ending with .csv
saved_titles_path = "./titles_so_far.pkl"

def hover_navbar(driver, actions, href_name, second_level_href_to_click=None):
    '''
        Hover the navbar element and get the occured list.
        If a second href is provided, click to that and navigate.
    '''

    try:
        WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.ID, "nmenu"))
            )
    except:
        driver.quit()

    navbar_element = driver.find_element(By.XPATH, "//a[contains(@href,'"+href_name+"')]")
    driver.execute_script("arguments[0].scrollIntoView(true);", navbar_element)
    time.sleep(2)
    actions.move_to_element(navbar_element).perform()

    if second_level_href_to_click != None:
        second_navbar_element = driver.find_element(By.XPATH, "//a[contains(@href,'"+second_level_href_to_click+"')]")
        actions.move_to_element(second_navbar_element).click().perform()

def get_movies_from_list(driver, actions, list_class):

    try:
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.ID, "nwrap"))
        )
    except:
        print("omg")
        driver.quit()

    row_locator = "//td[contains(@class,'rowbeyaz')]/parent::tr//a"
    rows = WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.XPATH, row_locator)))
    
    # deduplicate
    elements = []
    for i, row in enumerate(rows):
        innerHTML = row.get_attribute("innerHTML")
        if "span" in innerHTML:
            elements.append(row)

    return elements
        
def visit_movies(elements, actions, driver):
    # add the titles you have visited
    if os.path.exists(saved_titles_path):
        with open(saved_titles_path, "rb") as f:
            titles_so_far = pickle.load(f)
            f.close()
    else:
        titles_so_far = []

    for i in range(len(elements)):
        row = elements[i]
        title = row.get_attribute("title")
        driver.execute_script("arguments[0].scrollIntoView(true);", row)
        time.sleep(2)
        if title in titles_so_far:
            continue
        else:
            if row.is_displayed():
                print("moving")
                actions.move_to_element(row).click().perform()
                time.sleep(2)
                # download subtitles
                is_downloaded = download_subtitles_from_movie_page(actions, driver, title)
                print("DOWNLOADED ALL")
                # add to visited list if successful
                if is_downloaded:
                    titles_so_far.append(title)

                hover_navbar(driver, actions, href_name="/dizi/A/1", second_level_href_to_click="/imdb250dizi.html")
                elements = get_movies_from_list(driver, actions, list_class="rowbeyaz")
                if i == 2:
                    with open(saved_titles_path, "wb") as fw:
                        pickle.dump(titles_so_far, fw)
                    driver.quit()

def rename_latest(new_name, path):
    list_of_files = glob.glob(path_a)
    latest_file = max(list_of_files, key=os.path.getctime)
    #prints a.txt which was latest file i created
    os.rename(latest_file, path+"/"+new_name)

def extract_intersected_rips(turkish_rip_types, english_rip_types):
    intersection_rips = list(set(turkish_rip_types).intersection(set(english_rip_types)))

    if intersection_rips != []:
        return intersection_rips[0]
    else:
        for tr_rip in turkish_rip_types:
            tr_rip_shortcut = tr_rip.replace("\t", "").replace("\n", "").replace("  ", "")
            for en_rip in english_rip_types:
                en_rip_shortcut = en_rip.replace("\t", "").replace("\n", "").replace("  ", "")

                if tr_rip_shortcut in en_rip_shortcut:
                    intersection_rips = [tr_rip, en_rip]
                    return intersection_rips
                elif en_rip_shortcut in tr_rip_shortcut:
                    intersection_rips = [tr_rip, en_rip]
                    return intersection_rips
        return None

def download_subtitles_from_movie_page(actions, driver, title):

    # get the season links
    locator = "//div[contains(@class,'altyazi-list-wrapper')]//a[contains(@class, 'new-toggle')]"
    rows = driver.find_elements(By.XPATH, locator)
    if rows == None:
        num_of_seasons = 1
    else:  
        num_of_seasons = len(rows) // 2

    print("NUM SEASONS OF THE TV SHOW: ", num_of_seasons)

    sub_page_element = driver.find_element(By.XPATH, ".//div[contains(@class, 'sub-container nleft')]//a[contains(@data-href, 'altyazilar')]")
    actions.move_to_element(sub_page_element).click().perform()
    time.sleep(1)

    for season in range(num_of_seasons, 0, -1):

        season_tag = "sezon_"+str(season)
        season_locator_id = "sz_"+str(season)
        # click to the season
        season_locator = "//div[contains(@class,'pagin ta-container mb4')]/a[contains(@id, '"+season_locator_id+"')]"
        season_element = driver.find_element(By.XPATH, season_locator)
        driver.execute_script("arguments[0].scrollIntoView(true);", season_element)
        time.sleep(2)
        actions.move_to_element(season_element).click().perform()
        time.sleep(1)

        locator = "//div[contains(@class,'altyazi-list-wrapper')]//span[contains(@class, 'flagtr')]/ancestor::div[contains(@class, '"+season_tag+"')]"
        turkish_sub_rows = WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.XPATH, locator)))

        locator = "//div[contains(@class,'altyazi-list-wrapper')]//span[contains(@class, 'flagen')]/ancestor::div[contains(@class, '"+season_tag+"')]"
        english_sub_rows = WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.XPATH, locator)))

        turkish_rip_types = []
        for row in turkish_sub_rows:
            rip_type = row.find_element(By.XPATH, ".//div[contains(@class, 'ripdiv')]").text
            #rip_type = rip_type.replace("\t", "").replace("\n", "").replace("  ", "")
            turkish_rip_types.append(rip_type)
        
        english_rip_types = []
        for row in english_sub_rows:
            rip_type = row.find_element(By.XPATH, ".//div[contains(@class, 'ripdiv')]").text
            #rip_type = rip_type.replace("\t", "").replace("\n", "").replace("  ", "")
            english_rip_types.append(rip_type)

        intersection_rips = extract_intersected_rips(turkish_rip_types, english_rip_types)

        if intersection_rips:
            if isinstance(intersection_rips, list):
                one_rip_tr = intersection_rips[0]
                one_rip_en = intersection_rips[1]
            elif isinstance(intersection_rips, str):
                one_rip_tr = intersection_rips
                one_rip_en = intersection_rips

        if intersection_rips:
            
            # Download Turkish Subtitles
            index_turkish = turkish_rip_types.index(one_rip_tr)
            href_to_tr_sub = turkish_sub_rows[index_turkish].find_element(By.XPATH, ".//a[contains(@itemprop, 'url')]")

            driver.execute_script("arguments[0].scrollIntoView(true);", href_to_tr_sub)
            time.sleep(2)

            actions.move_to_element(href_to_tr_sub).click().perform()
            time.sleep(1)
            
            download_button = driver.find_element(By.XPATH, "//button[contains(@class, 'altIndirButton')]")
            actions.move_to_element(download_button).click().perform()
            time.sleep(3)
            rename_latest(title.replace(" ", "").replace("/", "")+"_"+rip_type.replace("\t", "").replace("\n", "").replace(" ", "").replace("/", "")+"_TR_season_"+str(season), path)

            driver.back()
            time.sleep(3)
            # Download English Subtitles
            index_english = english_rip_types.index(one_rip_en)
            href_to_en_sub = english_sub_rows[index_english].find_element(By.XPATH, ".//a[contains(@itemprop, 'url')]")
            driver.execute_script("arguments[0].scrollIntoView(true);", href_to_en_sub)
            time.sleep(2)

            actions.move_to_element(href_to_en_sub).click().perform()
            time.sleep(1)
            
            download_button = driver.find_element(By.XPATH, "//button[contains(@class, 'altIndirButton')]")
            actions.move_to_element(download_button).click().perform()
            time.sleep(3)
            rename_latest(title.replace(" ", "").replace("/", "")+"_"+rip_type.replace("\t", "").replace("\n", "").replace(" ", "").replace("/", "")+"_EN_season_"+str(season), path)
            driver.back()
            time.sleep(2)

    return True


driver = webdriver.Safari()
driver.get("https://turkcealtyazi.org/index.php")
driver.maximize_window()
actions = ActionChains(driver)

hover_navbar(driver, actions, href_name="/dizi/A/1", second_level_href_to_click="/imdb250dizi.html")
elements = get_movies_from_list(driver, actions, list_class="rowbeyaz")
visit_movies(elements, actions, driver)
driver.quit()



