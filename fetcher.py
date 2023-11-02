# -*- coding: UTF-8 -*-

"""
Author: Pierre PCJRS
Updated: Fall 2023
"""

import os
import sys
import time
import pandas as pd
import getpass
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
#New Additions
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.firefox import GeckoDriverManager
#Other
from configs.config import cfg
from utils import timenow

class GradeBot:
    def __init__(self, username, password):
        """Gradebot! Your automated MyConcordia grade checker. For those stressful times
        where you are obsessively checking your grades that always seem to come out way later than expected :P

        Arguments:
            username {string} -- MyConcordia username
            password {string} -- MyConcordia password
        """
        self.username = username
        self.password = password
        opts = webdriver.FirefoxOptions()
        opts.headless = True
        self.bot = webdriver.Firefox(options=opts)


    def login(self):
        """Uses username and password to login to the student portal.
        """
        # Goto site
        bot = self.bot
        bot.get("https://campus.concordia.ca")
        time.sleep(1)

        # print("Logging in...")

        # Locate and populate user and pwd fields.
        user_field = bot.find_element(By.ID,'userNameInput')
        pwd_field = bot.find_element(By.ID,'passwordInput')
        
        #Populate Login Fields
        user_field.clear()
        pwd_field.clear()
        user_field.send_keys(self.username)
        pwd_field.send_keys(self.password)
        pwd_field.send_keys(Keys.RETURN)
        time.sleep(6)

        #Test if login success or not
        if bot.current_url == 'https://campus.concordia.ca/psc/pscsprd/EMPLOYEE/SA/c/SA_LEARNER_SERVICES.SSS_STUDENT_CENTER.GBL':
            pass
        else:
            print('Current URL:', bot.current_url)
            print('Login failed.')
            print('Re-run the program.')
            sys.exit(1)
        print("✓ Login SUCCESS.")

        # Goto student center and find grades
        bot.find_element(By.ID, 'submenu-button-1').click()
        time.sleep(2)
        bot.find_element(By.CSS_SELECTOR, 'a[data-select-value="1030"]').click()
        time.sleep(4)
        #print('Current URL:', bot.current_url)
        print("✓ Grade Page ACCESSED.")


        #List array of semesters

        #Find the HTML code block of the grades table    
        html_code = bot.find_element(By.ID, 'SSR_DUMMY_RECV1$scroll$0').get_attribute('outerHTML')

        # Parse the HTML
        soup1 = BeautifulSoup(html_code, 'html.parser')

        # Find all elements with IDs containing 'TERM_CAR$'
        term_elements = soup1.find_all('span', {'id': lambda x: x and 'TERM_CAR$' in x})

        # Extract the terms and create table
        terms_data = {
            'Term': [element.text for element in term_elements],
        }
        df_terms_data = pd.DataFrame(terms_data)
        self.Term_List = df_terms_data['Term'].values

        
        #Print the available terms for user
        print('✓ Terms list SUCCESS. \n', df_terms_data['Term'])
        self.semester = input('Semester: ')
        


    def goto_grades(self, old_format=False):
        """Get to grade section after clicking on the radio button corresponding to the user input for 'semester'.

        Arguments:
            semester {String} -- Semester from Fall 2016 to Winter 2020.
            old_format {bool} -- Perform additional button click post-app update.
        """
        #df_terms_data = pd.DataFrame(self.df_terms_data)
        bot = self.bot
        
        # Change semester view.
        if not old_format:
            time.sleep(2)

        # Semester selection
        if self.semester not in self.Term_List:
            print('Unsupported/invalid semester. Choose semester between Fall 2015 and Winter 2023.')
            sys.exit(1)

        idval = self.Term_List.tolist().index(self.semester)
        chosen_id = "SSR_DUMMY_RECV1$sels$" + str(idval) + "$$0"
        bot.find_element(By.ID,chosen_id).click()
        print('✓ Found ', self.semester, 'Term SUCCESS.')

    def output_vmg(self):
        """Output what is seen at 'view my grades' on myconcordia portal.
        """
        bot = self.bot

        # GRADES
        bot.find_element(By.XPATH, "//li[@data-gh-page-link='SSR_SSENRL_TERM' and @data-gh-item-link='DERIVED_SSS_SCT_SSR_PB_GO']//a").click()
        #print('Success line 117')

        # Save current url to html
        time.sleep(1.5)
        with open('grades.html', 'w') as f:
            f.write(bot.page_source)
        site = os.getcwd() + '/grades.html'
        page = open(site)
        soup = BeautifulSoup(page.read(), features="html.parser")
        #os.remove('grades.html')
        #print('Success line 127')

        # Parse
        grades = []
        table = soup.find('table', {'class': 'PSLEVEL1GRIDWBO'})
        table_body = table.find('tbody')
        rows = table_body.find_all('tr')
        for row in rows:
            cols = row.find_all('td')
            cols = [ele.text.strip() for ele in cols]
            grades.append([ele for ele in cols])
            #print('Success line 139')

        # Convert to dataframe
        grades_df = pd.DataFrame(grades).drop([0])
        unwanted = [x for x in range(6, len(grades_df.columns))]
        grades_df = grades_df.drop(grades_df.columns[unwanted], axis=1)
        grades_df = grades_df.drop([1])
        grades_df.columns = ['Class', 'Description',
                             'Units', 'Grading', 'Letter Grade', 'Grade Points']
        #print('Success line 146')

        # DISTRIBUTION
        bot.find_element(By.CLASS_NAME, 'toggle.fa.fa-angle-down.label-false.ui-btn.gh-btn').click()
        bot.find_element(By.LINK_TEXT,'Grade Distribution').click()
        #print('Success line 151')

        time.sleep(1.5)
        with open('dist.html', 'w') as f:
            f.write(bot.page_source)
            #print('Success line 156')

        site = os.getcwd() + '/dist.html'
        page = open(site)
        soup = BeautifulSoup(page.read(), features="html.parser")
        #os.remove('dist.html')
        print('SUCCESS line 192')

        # Parse distribution table
        dist = []
        table = soup.find('table', {'class': 'PSLEVEL1GRID'})
        table_body = table.find('tbody')

        rows = table_body.find_all('tr')
        for row in rows:
            cols = row.find_all('td')
            cols = [ele.text.strip() for ele in cols]
            dist.append([ele for ele in cols])

        # Convert to dataframe
        dist_df = pd.DataFrame(dist)
        dist_df.columns = ['Class', 'A+', 'A', 'A-', 'B+', 'B', 'B-',
                           'C+', 'C', 'C-', 'D+', 'D', 'D-', 'F', 'FNS', 'R', 'NR']

        return grades_df, dist_df   
        bot.quit


    def goto_newsearch(self):
        """Output a new semester on myconcordia portal.
        """
        bot = self.bot

        # See other Terms
        user_input = input('Would you like to see other term (Yes/No): ')
        
        if user_input.lower() == 'yes':
            # Code to handle 'Yes' case
            bot.find_element(By.XPATH, "//li[@data-gh-page-link='SSR_SSENRL_GRADE' and @data-gh-item-link='DERIVED_SSS_SCT_SSS_TERM_LINK']//a/span").click()
            os.system('cls' if os.name == 'nt' else 'clear')
            print('User wants to see other term.')
        else:
            bot.quit()


    def send_message(self, grades_table, distribution_table, bot_pwd):
        """SMTP/ESMTP client for automated emails.

        Arguments:
            grades_table {dataframe} -- Grade table
            distribution_table {dataframe} -- Grade distribution table
            bot_pwd {string} -- Sender email password
        """

        # General setup
        msg = MIMEMultipart()
        msg['From'] = cfg['source_email']
        msg['To'] = cfg['target_email']
        msg['Subject'] = "New Grade!"

        # Structure the tables to be featured in the email.
        table1 = """
        <html>
          <head></head>
          <body>
            {0}
          </body>
        </html>
        """.format(grades_table.to_html())

        whitespace = """
        <html>
          <head></head>
          <body>
            
          </body>
        </html>
        """

        table2 = """\
        <html>
          <head></head>
          <body>
            {0}
          </body>
        </html>
        """.format(distribution_table.to_html())
        msg.attach(MIMEText(table1, 'html'))
        msg.attach(MIMEText(whitespace, 'html'))
        msg.attach(MIMEText(table2, 'html'))

        # Send the message and quit.
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(msg['From'], bot_pwd)
        text = msg.as_string()  # You now need to convert the MIMEMultipart object to a string to send
        server.sendmail(msg['From'], msg['To'], text)
        print('SUCCESS - Message Sent')
        server.quit()

if __name__ == '__main__':

    # Accept user input for username, passwords and semester
    #user = input('Username: ')
    user = 'P_Gacett'
    #pwd = getpass.getpass()
    pwd = 'Burnout5!'
    #bot_pwd = getpass.getpass() #d7
    checker = GradeBot(user, pwd)
    old_grades = pd.DataFrame({"Letter Grade": ["", "", "", ""]})

    while True:
        # Instantiate bot with command-line-args and login
        checker = GradeBot(user, pwd)
        checker.login()

        # Fetch grades
        checker.goto_grades()
        grades, distribution = checker.output_vmg()
        
        # Print tables depending on config option.
        if cfg['options']['console_log_tables']:
            print(grades.to_string(index=False) + '\n\n' + distribution.to_string(index=False) + '\n')

        # Compare to previous version and send email if different.
        if cfg['options']['email_notification']:
        	if list(grades['Letter Grade']) != list(old_grades['Letter Grade']):
        		checker.send_message(grades, distribution, pwd) #bot_pwd)
        		print(timenow() + "******Email sent.")
        	else:
        		print(timenow() + "No changes detected.")
        else:
        	sys.exit(0)

        # Store copy of previous grade matrix for future comparisons.
        old_grades = grades.copy()

        # Run every 30 min
        time.sleep(cfg['options']['time_interval'])

        #See other semesters
        #checker.goto_newsearch()
