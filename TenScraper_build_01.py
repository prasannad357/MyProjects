#    C:\Users\Prasanna\Downloads
from selenium import webdriver
from selenium.webdriver.support.ui import Select
from bs4 import BeautifulSoup
from PIL import Image
import time
import requests
import os
import shutil

wait = 5
more_wait = 7
less_wait = 4
download_time = 20

shutil.rmtree("./temp")

# Gets website details, Minimum EMD/Tender Value, Category from the user, open the browser and website

web_num = int(input("""Please enter the tender website number you want data to be fetched from:
1. E-procure/CPP portal (https://eprocure.gov.in/eprocure/app)
2. Mahatender (https://mahatenders.gov.in/nicgep/app)
3. E-tenders (https://etenders.gov.in/eprocure/app)

Please enter option from 1 to 3:\n"""))
web = ["https://eprocure.gov.in/eprocure/app","https://mahatenders.gov.in/nicgep/app","https://etenders.gov.in/eprocure/app"]
category_num = int(input("""Please select one of the following categories:
1. Furniture/ Fixture
2. Medical Equipments/Waste
3. Laboratory and scientific equipment
 """))
category = ["Furniture/ Fixture","Medical Equipments/Waste","Laboratory and scientific equipment"]
criteria_num = int(input("""Please select the approximate minimum tender value:
1. Rs. 0
2. Rs. 0.5 Lakh
3. Rs. 1 Lakh
4. Rs. 2 Lakh
5. Rs. 5 Lakh

Please enter option from 1 to 5:\n"""))
download_folder = ""
temp_fold = input("\nPlease enter the address of download folder from disk:\n")

# Removes escape character from download folder path
for eachChar in temp_fold:
    if (eachChar == temp_fold[-1]) and (eachChar == "\\"):
        break
    if eachChar == "\\":
        download_folder += "/"
        continue
    download_folder += eachChar

print("Download folder path:",download_folder)

if download_folder[-1] == '/':
    download_folder[-1] == ""

criteria = ["0","50,000","1,00,000","2,00,000","4,00,000"]
raw_captcha = ""
captcha = ""
# Open primary browser
browser = webdriver.Chrome()
browser.get(web[web_num - 1]) #Get the website url from the list
time.sleep(2)

# Open "Search" option, enter the category, read and enter the CAPTCHA
search = browser.find_element_by_link_text("Search") #Find "search"
time.sleep(2)
search.click() #click on Search option
time.sleep(1)

# Take SS and crop it
def screenshot_crop(x1=737,y1=600,x2=1010,y2=704):
    print("\n\nTaking a screenshot...\n\n")
    browser.save_screenshot("screenshot.png")
    screenshot = Image.open("screenshot.png")
    captcha_search = screenshot.crop((x1,y1,x2,y2))
    captcha_search.save("captchaSearch.png","PNG")
    screenshot.close()

# Open new window/tab, open OCR, upload SS and read the text, return text
def get_raw_captcha():
    print("\n\nGetting raw captcha...\n\n")
    temp = webdriver.Chrome()
    temp.get("https://www.onlineocr.net")
    time.sleep(3)
    temp.find_element_by_xpath("//span/input[@id='fileupload']").send_keys("C:/Users/Prasanna/web_scraping/TenScraper/captchaSearch.png")
    time.sleep(4)
    temp.find_element_by_id("MainContent_btnOCRConvert").click()
    time.sleep(20)
    temp_html = temp.page_source
    temp_soup = BeautifulSoup(temp_html,"lxml")
    # print(temp_soup.prettify())
    time.sleep(15)
    raw_captcha = str(temp_soup.find("textarea",id = "MainContent_txtOCRResultText").text)
    print(raw_captcha)
    temp.close()
    return raw_captcha

# USED IN PROCESS_CAPTCHA(). Takes in raw_captcha, removes all random symbols that are in it and keeps only 0-9, A-Z, a-Z characters in it,
# returns the captcha
def make_captcha(raw_captcha):
    captcha = ''
    for count in range(len(raw_captcha)):
        if(ord(raw_captcha[count]) in range(48,58)) or (ord(raw_captcha[count]) in range(65,91)):
            captcha = captcha + raw_captcha[count]
        else:
            continue
    return captcha

#Asks user for captcha
def manual_captcha():
    return input("\n*******************\nPlease check the browser and enter the captcha here:\n*******************\n")

# Fills search form
def search_form():
    print("\n\nFilling tender details in search form...\n\n")
    tender_type = Select(browser.find_element_by_id("TenderType"))
    time.sleep(wait)
    tender_type.select_by_visible_text("Open Tender")
    time.sleep(wait)
    product_category = Select(browser.find_element_by_id("ProductCategory"))
    time.sleep(wait)
    product_category.select_by_visible_text(category[category_num - 1])
    time.sleep(wait)
    browser.find_element_by_xpath("//input[@id='captchaText']").send_keys(captcha)
    time.sleep(wait)
    browser.find_element_by_xpath("//input[@id='submit']").click()
    time.sleep(wait)

# Refreshes captcha if the captcha made from raw_captcha doesn't have 6 characters
def process_captcha(raw_captcha):
    print("\n\nProcessing captcha...\n\n")
    for count in range(2):
        captcha = make_captcha(raw_captcha)
        if len(captcha) == 6:
            break
        if len(captcha) != 6:
            time.sleep(wait)
            browser.find_element_by_xpath("//button[@id='captcha']").click()
            time.sleep(wait)
            screenshot_crop()
            time.sleep(wait)
            raw_captcha = get_raw_captcha()
            continue
    if len(captcha) != 6:
        captcha = manual_captcha()
    return captcha

# Checks for error, returns True if there's an error on the page, returns False, if there's no error
def search_check():
    print("\n\nChecking for errors...\n\n")
    try:
        main_html = browser.page_source
        main_soup = BeautifulSoup(main_html,"lxml")
        err = main_soup.find(class_="error").text
        print(err)
        return True
    except:
        return False

# Gets all tender links
def get_tender_links():
    print("\n\nGetting all tender links...\n\n")
    time.sleep(wait)
    tender_links = [browser.find_element_by_id("DirectLink_0").get_attribute("href")]
    time.sleep(wait)
    base_id = "DirectLink_0_"
    modifier = 0
    while(True):
        try:
            time.sleep(wait)
            tender_links.append(browser.find_element_by_id(base_id+str(modifier)).get_attribute("href"))
            time.sleep(wait)
            modifier += 1
        except:
            break
    print(tender_links)
    return tender_links

#Checks if CAPTCHA is present on the page
def captcha_presence(browser):
    print("\n\nChecking if the page has asked for captcha...\n\n")
    try:
        time.sleep(wait)
        main_html = browser.page_source
        time.sleep(wait)
        main_soup = BeautifulSoup(main_html,"lxml")
        time.sleep(wait)
        browser.find_element_by_xpath("//input[@id='captchaText']")
        time.sleep(wait)
        return True
    except:
        return False

# Downloads PDF and ZIP files
def get_pdf(url,folder):
    print("\n\nGetting Tender notice pdfs!!!\n\n")
    browser.find_element_by_link_text("Tendernotice_1.pdf").click()
    time.sleep(download_time)
    browser.find_element_by_link_text("Download as zip file").click()
    time.sleep(download_time)
    for root,dir,files in os.walk(download_folder):
        for file in files:
            if file.endswith('.zip') and file[0] == 'w'and file[1] == 'o' and file[2] == 'r' and file[3] == 'k':
                zip = str(file)
                break
    time.sleep(wait)
    try:
        os.makedirs(f"./temp/{folder}") # This will throw FileExistsException if folder already exists
        os.replace(download_folder+"/Tendernotice_1.pdf",f"./temp/{folder}/Tendernotice_1.pdf")
        os.replace(download_folder+"/"+zip,f"./temp/{folder}/{zip}")
    except:  #delete the folder and then run makedirs
        shutil.rmtree(f"./temp/{folder}")
        os.makedirs(f"./temp/{folder}")
        os.replace(download_folder+"/Tendernotice_1.pdf",f"./temp/{folder}/Tendernotice_1.pdf")
        os.replace(download_folder+"/"+zip,f"./temp/{folder}/{zip}")

# Enters CAPTCHA that needs to be entered after clicking on download option
def download_captcha():
    print("\n\nEntering captcha for download page...\n\n")
    base_id = "DirectLink_0_"
    modifier = 0
    while(True):
        time.sleep(wait)
        temp_link = browser.find_element_by_id(base_id+str(modifier)).get_attribute("href")
        time.sleep(wait)
        browser.execute_script(f"window.open('{temp_link}')")
        time.sleep(wait)
        browser.switch_to.window(browser.window_handles[-1])
        time.sleep(wait)

        if not(search_check()):
            browser.find_element_by_link_text("Tendernotice_1.pdf").click()

            if (captcha_presence(browser)):
                screenshot_crop(737,330,1010,425)   # enter crop co-ordinates i.e. x1,y1,x2,y2
                time.sleep(more_wait)
                raw_captcha = get_raw_captcha()
                time.sleep(more_wait)
                print("Raw captcha for download file is:",raw_captcha)
                captcha = process_captcha(raw_captcha)     # make captcha from raw captcha
                time.sleep(wait)
                browser.find_element_by_xpath("//input[@id='captchaText']").send_keys(captcha)  # Enter the captcha
                time.sleep(wait)
                browser.find_element_by_xpath("//input[@id='Submit']").click()
                time.sleep(wait)
                err = search_check()                 #Check if captcha was correct

                if err:
                    captcha = manual_captcha()
                    time.sleep(wait)
                    browser.find_element_by_xpath("//input[@id='captchaText']").send_keys(captcha)
                    time.sleep(wait)
                    browser.find_element_by_xpath("//input[@id='Submit']").click()
                    time.sleep(wait)

                browser.execute_script("window.close()")
                browser.switch_to.window(browser.window_handles[0])
                break

        browser.execute_script("window.close()")
        browser.switch_to.window(browser.window_handles[0])
        modifier += 1

# Opens tender links to get tender details and to download the file
def get_tender_details():
    print("\n\nTime to get all the tender details!!\n\n")
    download_captcha()
    link_count = 0
    folder = 0
    tender_links = get_tender_links()
    time.sleep(wait)

    for tender_link in tender_links:
        print(tender_link)
        time.sleep(more_wait)
        tend_link = f"window.open('{tender_link}')"
        time.sleep(wait)
        browser.execute_script(tend_link)
        #Switch to new window
        time.sleep(more_wait)
        browser.switch_to.window(browser.window_handles[-1])
        time.sleep(more_wait)
        #Captcha page will appear for the first time, Enter the captcha
        
        if not(search_check()):  # Check if download is available or not
            # browser.find_element_by_link_text("Tendernotice_1.pdf").click()
            folder += 1
            # os.makedirs(f"./temp/{folder}")
            url = browser.find_element_by_link_text("Tendernotice_1.pdf").get_attribute("href")
            get_pdf(url,folder)
            time.sleep(wait)
        browser.execute_script("window.close()")
        browser.switch_to.window(browser.window_handles[0])


screenshot_crop()
raw_captcha = get_raw_captcha()
captcha = process_captcha(raw_captcha)
search_form()
err = search_check()
print(err)

if err:
    captcha = manual_captcha()
    browser.find_element_by_xpath("//input[@id='captchaText']").send_keys(captcha)
    time.sleep(wait)
    browser.find_element_by_xpath("//input[@id='submit']").click()
    time.sleep(wait)

get_tender_details()
print("\n*****************************************\n")
print("ALL DONE!!!")
print("\n*****************************************\n")
time.sleep(10)
browser.close()
