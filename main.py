import json
import re
import sqlite3
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from lib.google_source import Google

CONFIG_FILE = 'config.json'

def get_rows(mint_username, mint_password, google):
    driver = webdriver.Chrome()
    time.sleep(1)

    driver.get('http://www.mint.com')
    time.sleep(5)

    login = [a for a in driver.find_elements_by_tag_name('a') if 'Sign in' in a.text][0]
    login.click()
    time.sleep(5)

    userid = driver.find_element_by_id('ius-userid')
    userid.send_keys(mint_username)
    password = driver.find_element_by_id('ius-password')
    password.send_keys(mint_password)
    driver.find_element_by_id('ius-sign-in-submit-btn-text').click()
    time.sleep(5)

    try:
        driver.find_element_by_id('ius-label-mfa-send-an-email-to').click()
        driver.find_element_by_id('ius-mfa-options-submit-btn').click()
       
        time.sleep(30)
        snippet = google.get_first_message_snippet()
        code = re.findall('\d{3,}', snippet)[0]
        
        code_input = driver.find_element_by_id('ius-mfa-confirm-code')
        code_input.send_keys(code)
        driver.find_element_by_id('ius-mfa-otp-submit-btn').click()
        time.sleep(5)
    except NoSuchElementException:
        pass

    driver.get('https://mint.intuit.com/transaction.event')
    time.sleep(15)

    rows = driver.find_element_by_xpath("//table[@id='transaction-list']").find_elements_by_class_name('pending')
    rows_formatted = []
    for row in rows:
        tr_id = row.get_attribute('id')
        date = row.find_element_by_class_name('date').text
        description = row.find_element_by_class_name('description').text
        money = row.find_element_by_class_name('money').text
        rows_formatted.append((tr_id, '{0} - {1} - {2}'.format(date, description, money)))

    time.sleep(1)
    driver.close()
    return rows_formatted

def setup_db():
    conn = sqlite3.connect('mint.db')
    cursor = conn.cursor()
    try:
        cursor.execute('CREATE TABLE pending_trxs (id, trx)')
    except sqlite3.OperationalError:
        pass
    conn.commit()
    conn.close()

def get_sql_connection():
    return sqlite3.connect('mint.db')

def get_previous_rows():
    conn = get_sql_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM pending_trxs')
    rows = cursor.fetchall()
    conn.commit()
    conn.close()
    return rows

def get_differences(rows, not_in):
    trx_ids = set([row[0] for row in not_in])
    return [row for row in rows if row[0] not in trx_ids]

def get_new_rows(rows):
    previous_rows = get_previous_rows()
    return get_differences(rows, previous_rows)

def get_old_rows(rows):
    previous_rows = get_previous_rows()
    return get_differences(previous_rows, rows)

def update_db(old_rows, new_rows):
    conn = get_sql_connection()
    cursor = conn.cursor()
    cursor.executemany('DELETE FROM pending_trxs WHERE id IN (?)', [(row[0],) for row in old_rows])
    cursor.executemany('INSERT INTO pending_trxs VALUES (?, ?)', new_rows)
    conn.commit()
    conn.close()

def get_config(config_file):
    keys = ['google_client_id', 'google_client_secret', 'from_email', 'to_email', 'mint_username', 'mint_password']
    config = {}
    with open(config_file, 'r') as f:
        data = json.loads(f.read())
        for key in keys:
            config[key] = data[key] if key in data else ''
    return config

def format_rows(rows):
    rows_formatted = '\n'.join([row[1] for row in rows])
    return 'New transactions:\n\n{0}'.format(rows_formatted)

config = get_config(CONFIG_FILE)
google = Google(
        CONFIG_FILE,
        config['google_client_id'],
        config['google_client_secret'],
        config['from_email'],
        '',
        ''
)
google.setUp()

rows = get_rows(config['mint_username'], config['mint_password'], google)
new_rows = get_new_rows(rows)
old_rows = get_old_rows(rows)
print(google.send_message(format_rows(old_rows), config['to_email']))
update_db(old_rows, new_rows)
