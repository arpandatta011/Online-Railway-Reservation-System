import streamlit as st
from numpy import int8
import pandas as pd
import streamlit as st
import time, random
import datetime as dt
import mysql.connector as mysql


mydb = mysql.connect(host="localhost",user="root",passwd="password",database='online_railway_db')
sql = mydb.cursor()
pass_df = pd.read_sql('SELECT * FROM passengers', con=mydb)
login_df = pd.read_sql('SELECT * FROM login', con=mydb)
train_df = pd.read_sql('SELECT * FROM train', con=mydb)
ticket_df = pd.read_sql('SELECT * FROM ticket', con=mydb)


headersection = st.container()
loginsection = st.container()
registersection = st.container()
mainsection = st.container()


def show_main_page():
    
    with mainsection:
        
        st.sidebar.title('Menu')
        
        page = st.sidebar.radio('',('Search Trains','Book Tickets','Cancel Tickets','Booking History','Edit Your Details','Reset Password','Logout'))


        if page == 'Search Trains':
            
            st.title('Search Train')
            source = st.selectbox('Source',options=['---']+train_df['Tr From'].unique().tolist())
            destination = st.selectbox('Destination',options=['---']+train_df[train_df['Tr From']==source]['Tr To'].unique().tolist())
            
            if source != '---' and destination != '---':
                train_df_filter = train_df[(train_df['Tr From'] == source) & (train_df['Tr To'] == destination)]
                train_df_filter = train_df_filter.reset_index(drop=True)
                train_df_filter = train_df_filter.drop(['Tr From','Tr To'],axis=1)
                train_df_filter = train_df_filter.rename(columns={'Tr Number':'Train Number','Tr Name':'Train Name','Tr Dept Time':'Source Time','Tr Arr Time':'Destination Time','Tr Total Seats':'Total Seats','Tr Avl Seats':'Available Seats'})
                st.dataframe(train_df_filter)


        elif page == 'Book Tickets':
            st.title('Book Tickets')

            pass_id = int(login_df[login_df['UserName']==st.session_state['username']]['Pass ID'].values[0])

            source = st.selectbox('Source',options=['---']+train_df['Tr From'].unique().tolist())
            destination = st.selectbox('Destination',options=['---']+train_df[train_df['Tr From']==source]['Tr To'].unique().tolist())
            
            train_df_filter = train_df[(train_df['Tr From'] == source) & (train_df['Tr To'] == destination)]
            train_df_filter['Tr Name'] = train_df_filter['Tr Number'].map(str) + ' - ' + train_df_filter['Tr Name']
            select_train = st.selectbox('Select Train',options=['---']+train_df_filter['Tr Name'].unique().tolist())
            train_number = select_train.split(' - ')[0]

            date = st.date_input('Date of Journey',min_value=dt.date.today())
            if select_train != '---':
                number_of_person = st.number_input('Number of Passengers',min_value=1,max_value=train_df_filter[train_df_filter['Tr Name']==select_train]['Tr Avl Seats'].values[0])
            else:
                number_of_person = st.number_input('Number of Passengers',min_value=0,max_value=0)

            number_of_person = int(number_of_person)
            seat_numbers_generated = []
            for i in range(number_of_person):
                seat_numbers_generated.append(random.randint(1,train_df_filter[train_df_filter['Tr Name']==select_train]['Tr Total Seats'].values[0]))
            seat_numbers = ' , '.join([str(i) for i in seat_numbers_generated])

            while True:
                ticket_number_generated = random.randint(100000,1000000)
                if ticket_number_generated not in ticket_df['Ticket Number'].values:
                    break
                
            if number_of_person != 0:
                total_price = number_of_person*train_df_filter[train_df_filter['Tr Name']==select_train]['Tr Price'].values[0]

                st.write('Total Price: ',total_price)

            if st.button('Pay and Book'):
                
                st.info('Payment Successful')
                sql.execute('INSERT INTO ticket (`Ticket Number`,`Pass ID`,`Tr Number`,`Date`,`Number of Pass`,`Seats Numbers`,`Total Prices`) VALUES (%s,%s,%s,%s,%s,%s,%s)',(int(ticket_number_generated),int(pass_id),train_number,date,number_of_person,seat_numbers,int(total_price)))
                mydb.commit()

                st.success('Ticket Booked Successfully')
                st.write('Your Ticket Number is : ',ticket_number_generated)
                st.write('Your Seat Numbers are : ',seat_numbers)



        elif page == 'Cancel Tickets':
            st.title('Cancel Ticket')
            pass_id = login_df[login_df['UserName']==st.session_state['username']]['Pass ID'].values[0]
            not_journed = ticket_df[ticket_df['Date']>dt.date.today()]
            not_journed = not_journed[not_journed['Pass ID']==pass_id]
            not_journed_ticket_number = not_journed['Ticket Number'].values
            ticket_number = st.selectbox('Select Ticket Number',options=['---']+not_journed_ticket_number.tolist())
            if ticket_number != '---':

                ticket_details = ticket_df[ticket_df['Ticket Number']==ticket_number]
                train_details = train_df[train_df['Tr Number']==ticket_details['Tr Number'].values[0]]
                merged = pd.merge(ticket_details,train_details,on='Tr Number')
                merged = merged[['Ticket Number','Tr Number','Tr Name','Tr From','Tr To','Date','Number of Pass','Seats Numbers','Total Prices']]
                merged = merged.rename(columns={'Tr Number':'Train Number','Tr Name':'Train Name','Tr From':'Source','Tr To':'Destination','Date':'Date of Journey','Number of Pass':'Number of Passengers','Seats Numbers':'Seat Numbers','Total Prices':'Total Price'})
                st.dataframe(merged)
                st.write('Are you sure you want to cancel the ticket?')
                if st.button('Yes'):

                    sql.execute('DELETE FROM ticket WHERE `Ticket Number` = %s',(ticket_number,))
                    mydb.commit()
                    st.success('Ticket Cancelled Successfully')
                    refund_msg = 'You will be refunded the amount of Rs. '+format(not_journed[not_journed['Ticket Number']==ticket_number]['Total Prices'].values[0])
                    st.info(refund_msg)

        elif page == 'Booking History':
            st.title('Booking History')
            pass_id = login_df[login_df['UserName']==st.session_state['username']]['Pass ID'].values[0]
            # join ticket and train table

            ticket_df_join = pd.merge(ticket_df[['Ticket Number','Pass ID','Tr Number']],train_df,on='Tr Number').merge(ticket_df.drop(['Tr Number','Pass ID'],axis=1),on='Ticket Number')
            #ticket_df_join = pd.concat([ticket_df_2[['Ticket Number','Tr Number']],train_df,ticket_df_2.drop(['Ticket Number'],axis=1)],axis=1,join='inner').drop_duplicates().reset_index(drop=True)
            ticket_df_join = ticket_df_join.rename(columns={'Tr Number':'Train Number','Tr Name':'Train Name','Tr Dept Time':'Source Time','Tr Arr Time':'Destination Time','Tr Total Seats':'Total Seats','Tr Avl Seats':'Available Seats'})
            # Booking History
            ticket_df_join = ticket_df_join[ticket_df_join['Pass ID']==pass_id]
            ticket_df_join = ticket_df_join.rename(columns={'Tr Name':'Train Name','Tr Dept Time':'Source Time','Tr Arr Time':'Destination Time','Tr Total Seats':'Total Seats','Tr Avl Seats':'Available Seats'})
            st.dataframe(ticket_df_join.drop('Pass ID',axis=1))




        elif page == 'Edit Your Details':

            st.title('Edit Your Details')

            pass_id = login_df[login_df['UserName']==st.session_state['username']]['Pass ID'].values[0]
            pass_df_filter = pass_df[pass_df['Pass ID']==pass_id]
            pre_name = pass_df_filter['Pass Name'].values[0]
            pre_age = pass_df_filter['Pass Age'].values[0]
            pre_gender = pass_df_filter['Pass Gender'].values[0]
            pre_address = pass_df_filter['Pass Address'].values[0]
            pre_contact = int(pass_df_filter['Pass Contacts'].values[0])
            
            if pre_gender == 'Male':
                gender_index = 0
            else :
                gender_index = 1

            name = st.text_input('Name',value=pre_name)
            age = st.text_input('Age',value=str(pre_age))
            gender = st.selectbox('Gender',['Male','Female'],index=gender_index)
            address = st.text_input('Address',value=pre_address)
            contact = int(st.text_input('Contact',value=str(pre_contact)))
            
            if st.button('Update'):
                sql.execute('update passengers set `Pass Name` = %s, `Pass Age` = %s, `Pass Gender` = %s, `Pass Address` = %s, `Pass Contacts` = %s where `Pass ID` = %s',(name,age,gender,address,contact,int(pass_id)))
                mydb.commit()
                st.success('Details updated successfully')
            
                



        elif page == 'Reset Password':
            st.title('Reset Password')
            
            password = st.text_input('Password', type='password')
            con_password = st.text_input('Confirm Password', type='password')
            if st.button('Reset'):
                if password == con_password:
                    sql.execute('UPDATE login SET Password = %s WHERE UserName = %s',(password,st.session_state['username']))
                    mydb.commit()
                    st.success('Password reset successful')
                else:
                    st.error('Passwords do not match')


        elif page == 'Logout':
            st.session_state['loggedIn'] = False
            st.success('Logged out')
            st.button('Login Again')
        



def registered():
   
    st.session_state['registered'] = True
    st.session_state['loggedIn'] = False


def need_login():
    st.session_state['registered'] = True



def show_register_page(*args):

    with registersection:
        with st.form('register_form'):
            st.markdown('### <center> **Register Now** </center>',unsafe_allow_html=True)
            name = st.text_input('Name',placeholder='Enter your name')
            if name == '':
                st.warning('Enter your name')
            elif len(name)<=3:
                st.warning('Name should be atleast 3 characters')
            age = st.text_input('Age',placeholder='Enter your age')
            if age == '':
                st.warning('Enter your age')
            else:
                try:
                    age = int(age)
                    if age < 18 or age > 100:
                        st.warning('Age should be between 18 and 100')
                except:
                    st.warning('Age should be a number')
            gender = st.selectbox('Gender',['Male','Female'])
            address = st.text_input('Address',placeholder='Enter Your Address')
            if address == '':
                st.warning('Enter your address')
            elif len(address)<=3:
                st.warning('Address should be atleast 3 characters')
            contact = st.text_input('Contact',placeholder='Enter Your Contact Number')
            if contact == '':
                st.warning('Enter your contact number')
            else:
                try:
                    contact = int(contact)
                    if len(str(contact))!=10:
                        st.warning('A contact number should be of 10 digits')
                    elif contact in pass_df['Pass Contacts'].values:
                        st.warning('This Contact number is already registered')
                except:
                    st.warning('A contact number should be of integers not characters')
            username = st.text_input('Set Username',placeholder='Enter Your Username')
            old_user_names = ['admin']+login_df['UserName'].values.tolist()
            if username == '':
                st.warning('Enter your username')
            elif len(username)<=3:
                st.warning('Username should be atleast 3 characters')
            elif username in old_user_names:
                st.warning('Username already exists')
            password = st.text_input('Set Password', type='password',placeholder='Enter Your Password')
            if password == '':
                st.warning('Enter your password')
            elif len(password)<=3:
                st.warning('Password should be atleast 3 characters')
            con_password = st.text_input('Confirm Password', type='password',placeholder='Confirm Your Password')
            if password != con_password:
                st.warning('Passwords do not match')
            agree = st.checkbox('I agree to the terms and conditions')
            if not agree:
                st.warning('You must agree to the terms and conditions')
            
            if st.form_submit_button('Register now'):
                if len(name) > 3 and len(address) > 3 and len(str(contact)) == 10 and len(username) > 3 and len(password) > 3 and password == con_password and agree:

                    try:
                        int(age)
                        int(contact)
                        if password == con_password and username not in old_user_names and age > 18 and age < 100: 
                            old_pass_ids = pass_df['Pass ID'].values.tolist()
                            sorted_pass_ids = sorted(old_pass_ids)
                            new_pass_id = sorted_pass_ids[-1] + 1
                            sql.execute('insert into passengers values (%s,%s,%s,%s,%s,%s)',(new_pass_id,name,age,gender,address,contact))
                            mydb.commit()
                            sql.execute('insert into login values (%s,%s,%s)',(new_pass_id,username,password))
                            mydb.commit()
                            st.success('Registration successful')
                                
                            st.form_submit_button('Continue to Login',on_click=registered)
                    
                    except:
                        pass
            
            st.markdown('<hr>',unsafe_allow_html=True)
             
            e1,e2 = st.columns([4,7])
                    
            e1.write('Already have an account?')

            e2.form_submit_button('Login Here',on_click=need_login)


            #st.markdown('<br>',True)
            
           




    

def need_register():
    st.session_state['registered'] = False
    

def show_login_page():
    with loginsection:
        with st.form('login_form'):
            st.markdown('### <center> **Login Now** </center>',unsafe_allow_html=True)
            username = st.text_input('Username')
            password = st.text_input('Password', type='password')
            #st.form_submit_button('Login',on_click=login,args=[username,password])  

            if st.form_submit_button('Login'):
                
                if username == 'admin' or password == 'admin':

                    st.session_state['admin_loggedIn'] = True
                    st.info('Logged in as admin')
                    st.form_submit_button('Continue to Admin Page')

                elif username in login_df['UserName'].values and password == login_df['Password'][login_df['UserName'] == username].values[0]:
                    st.session_state['loggedIn'] = True
                    st.session_state['username'] = username
                    st.success('Login successful')
                    st.form_submit_button('Continue to Main Page')
                    
                else:
                    st.warning('Username or Password is incorrect')
            st.markdown('<hr>',True)
            
            e1,e2 = st.columns([1.5,8.5])
                    
            e1.write('New User?')

            e2.form_submit_button('Register Here',on_click=need_register)


def show_admin_page():
    st.sidebar.title('Admin Menu')
        
    page = st.sidebar.radio('',('Show Trains','Show Users','Add Train','Edit Train','Remove Train', 'Remove User','Logout'))
    
    if page == 'Show Trains':
        st.subheader('Trains')
        train_df2 = train_df.rename(columns={'Tr Number':'Train Number','Tr Name':'Train Name','Tr From':'From','Tr To':'To','Tr Dept Time':'Departure','Tr Arr Time':'Arrival','Tr Total Seats':'Total Seats','Tr Avl Seats':'Available Seats','Tr Price':'Price'})
        st.table(train_df2)
    
    elif page == 'Show Users':
        st.subheader('Users')
        pass_df['Pass Contacts'] = pass_df['Pass Contacts'].astype('int64')
        pass_df2 = pass_df.rename(columns={'Pass ID':'Passenger ID','Pass Name':'Name','Pass Age':'Age','Pass Gender':'Gender','Pass Address':'Address','Pass Contacts':'Contact'})
        st.table(pass_df2)
    
    elif page == 'Add Train':
        st.subheader('Add Train')
        columns = train_df.columns
        train_number = st.text_input('Train Number',placeholder='00000')
        if train_number == '':
            st.warning('Enter train Number')
        elif int(train_number) in train_df['Tr Number'].values:
            st.warning('Train Number already exists')
        else:
            try:
                int(train_number)
                if len(train_number) != 5:
                    st.warning('Train Number should be 5 integers')
            except:
                st.warning('Train number should be a 5 integer not include any characters')
        
        train_name = st.text_input('Train Name',placeholder='Train')
        if train_name == '':
            st.warning('Enter train name')
        
        train_source = st.text_input('Train Source',placeholder='Station')

        if train_source == '':
            st.warning('Enter train source')
        
        train_destination = st.text_input('Train Destination',placeholder='Station')

        if train_destination == '':
            st.warning('Enter train destination')
        
        train_source_time = st.text_input('Train Source Time',placeholder='00.00 AM')

        if train_source_time == '':
            st.warning('Enter train source time')
        
        train_destination_time = st.text_input('Train Destination Time',placeholder='00.00 AM')

        if train_destination_time == '':
            st.warning('Enter train destination time')

        train_total_seats = st.text_input('Train Total Seats',placeholder='0')

        if train_total_seats == '':
            st.warning('Enter train total seats')
        else:
            try:
                int(train_total_seats)
            except:
                st.warning('Train total seats should be an integer')
        
        train_available_seats = train_total_seats

        train_fare = st.text_input('Train Fare',placeholder='0')

        if train_fare == '':
            st.warning('Enter train fare')
        else:
            try:
                int(train_fare)
            except:
                st.warning('Train fare should be an integer')
        

        if st.button('Add Train'):

            if train_number != '' and len(train_number) == 5 and train_name != '' and train_source != '' and train_destination != '' and train_source_time != '' and train_destination_time != '' and train_total_seats != '' and train_fare != '':
                try:
                    int(train_number)
                    int(train_total_seats)
                    int(train_fare)
                    # insert into mysql
                    sql.execute('insert into train values (%s,%s,%s,%s,%s,%s,%s,%s,%s)',(train_number,train_name,train_source,train_destination,train_source_time,train_destination_time,train_total_seats,train_available_seats,train_fare))
                    mydb.commit()
                    st.success('Train added successfully')
                except:
                    pass

    elif page == 'Edit Train':
        st.subheader('Edit Train')
        columns = train_df.columns
        train_number = st.text_input('Train Number',placeholder='00000')

        if train_number == '':
            st.warning('Enter train Number')
        elif int(train_number) not in train_df['Tr Number'].values:
            st.warning('Train Number does not exist')
        else:
            try:
                int(train_number)
                if len(train_number) != 5:
                    st.warning('Train Number should be 5 integers')
            except:
                st.warning('Train number should be a 5 integer not include any characters')

        # get previous values
        try:
            train_name = train_df['Tr Name'][train_df['Tr Number'] == int(train_number)].values[0]
            train_source = train_df['Tr From'][train_df['Tr Number'] == int(train_number)].values[0]
            train_destination = train_df['Tr To'][train_df['Tr Number'] == int(train_number)].values[0]
            train_source_time = train_df['Tr Dept Time'][train_df['Tr Number'] == int(train_number)].values[0]
            train_destination_time = train_df['Tr Arr Time'][train_df['Tr Number'] == int(train_number)].values[0]
            train_total_seats = train_df['Tr Total Seats'][train_df['Tr Number'] == int(train_number)].values[0]
            train_available_seats = train_df['Tr Avl Seats'][train_df['Tr Number'] == int(train_number)].values[0]
            train_fare = train_df['Tr Price'][train_df['Tr Number'] == int(train_number)].values[0]
        except:
            pass
        
        try:
            train_name = st.text_input('Train Name',value=train_name)
        except:
            train_name = st.text_input('Train Name',placeholder='Train')

        if train_name == '':
            st.warning('Enter train name')
        try:
            train_source = st.text_input('Train Source',value=train_source)
        except:
            train_source = st.text_input('Train Source',placeholder='Station')

        if train_source == '':
            st.warning('Enter train source')
        
        try:
            train_destination = st.text_input('Train Destination',value=train_destination)
        except:
            train_destination = st.text_input('Train Destination',placeholder='Station')

        if train_destination == '':
            st.warning('Enter train destination')

        try:
            train_source_time = st.text_input('Train Source Time',value=train_source_time)
        except:
            train_source_time = st.text_input('Train Source Time',placeholder='00.00 AM')

        if train_source_time == '':
            st.warning('Enter train source time')

        try:
            train_destination_time = st.text_input('Train Destination Time',value=train_destination_time)
        except:
            train_destination_time = st.text_input('Train Destination Time',placeholder='00.00 AM')

        if train_destination_time == '':
            st.warning('Enter train destination time')

        try:
            train_total_seats = st.text_input('Train Total Seats',value=train_total_seats)
        except:
            train_total_seats = st.text_input('Train Total Seats',placeholder='0')

        if train_total_seats == '':
            st.warning('Enter train total seats')
        else:
            try:
                int(train_total_seats)
            except:
                st.warning('Train total seats should be an integer')
        
        train_available_seats = train_total_seats

        try:
            train_fare = st.text_input('Train Fare',value=train_fare)
        except:
            train_fare = st.text_input('Train Fare',placeholder='0')

        if train_fare == '':
            st.warning('Enter train fare')
        else:
            try:
                int(train_fare)
            except:
                st.warning('Train fare should be an integer')

        if st.button('Edit Train'):
            if train_number != '' and len(train_number) == 5 and train_name != '' and train_source != '' and train_destination != '' and train_source_time != '' and train_destination_time != '' and train_total_seats != '' and train_fare != '':
                try:
                    int(train_number)
                    int(train_total_seats)
                    int(train_fare)
                    # insert into mysql
                    sql.execute('update train set `Tr Name` = %s, `Tr From` = %s, `Tr To` = %s, `Tr Dept Time` = %s, `Tr Arr Time` = %s, `Tr Total Seats` = %s, `Tr Avl Seats` = %s, `Tr Price` = %s where `Tr Number` = %s',(train_name,train_source,train_destination,train_source_time,train_destination_time,train_total_seats,train_available_seats,train_fare,train_number))
                    mydb.commit()
                    st.success('Train Updated successfully')
                except:
                    pass
                
    elif page == 'Remove Train':
        st.subheader('Remove Train')
        train_number = st.text_input('Train Number',placeholder='00000')

        if train_number == '':
            st.warning('Enter train Number')
        else:
            try:
                int(train_number)
                if len(train_number) != 5:
                    st.warning('Train Number should be 5 integers')
                        
                elif int(train_number) not in train_df['Tr Number'].values:
                    st.warning('Train Number does not exist')
            except:
                st.warning('Train number should be a 5 integer not include any characters')

        try:
            train_details = train_df[train_df['Tr Number'] == int(train_number)]
            train_details = train_details.rename(columns={'Tr Number':'Train Number','Tr Name':'Train Name','Tr From':'From','Tr To':'To','Tr Dept Time':'Departure','Tr Arr Time':'Arrival','Tr Total Seats':'Total Seats','Tr Avl Seats':'Available Seats','Tr Price':'Price'})
            st.table(train_details)
        except:
            pass 

        if st.button('Remove'):
            if train_number != '' and len(train_number) == 5:
                try:
                    int(train_number)
                    # delete associated records from ticket
                    sql.execute('delete from ticket where `Tr Number` = %s',(train_number,))
                    mydb.commit()
                    sql.execute('delete from train where `Tr Number` = %s',(train_number,))
                    mydb.commit()
                    st.success('Train deleted successfully')
                except:
                    pass
    
    elif page == 'Remove User':
        st.subheader('Remove User')

        pass_id = st.text_input('Passenger ID',placeholder='Passenger ID')

        if pass_id == '':
            st.warning('Enter passenger ID')
        else:
            try:
                int(pass_id)
                if int(pass_id) not in pass_df['Pass ID'].values:
                    st.warning('Passenger ID does not exist')
            except:
                st.warning('Passenger ID should not include any characters')

        try:
            pass_details = pass_df[pass_df['Pass ID'] == int(pass_id)]
            pass_details['Pass Contacts'] = pass_details['Pass Contacts'].astype('int64')
            pass_details = pass_details.rename(columns={'Pass ID':'Passenger ID','Pass Name':'Name','Pass Age':'Age','Pass Gender':'Gender','Pass Address':'Address','Pass Contacts':'Contact'})
            st.table(pass_details)
        except:
            pass

        if st.button('Remove'):
            if pass_id != '':
                try:
                    int(pass_id)
                    # delete associated records from ticket
                    sql.execute('delete from ticket where `Pass ID` = %s',(pass_id,))
                    mydb.commit()
                    sql.execute('delete from login where `Pass ID` = %s',(pass_id,))
                    mydb.commit()
                    sql.execute('delete from passengers where `Pass ID` = %s',(pass_id,))
                    mydb.commit()
                    st.success('Passenger deleted successfully')
                except:
                    pass





    elif page == 'Logout':
        st.session_state['admin_loggedIn'] = False
        st.success('Admin Logged out')
        st.button('Login Again')





with headersection:

    
    st.markdown('# <center> **Online Railway Reservation System** </center>',unsafe_allow_html=True)

    #first run will have nothing in session_state
    if 'registered' not in st.session_state or st.session_state['registered']:
        st.session_state['registered'] = True

        if 'loggedIn' not in st.session_state or 'admin_loggedIn' not in st.session_state:
            st.session_state['admin_loggedIn'] = False
            st.session_state['loggedIn'] = False
            show_login_page() 
        else:
            if st.session_state['admin_loggedIn']:
                st.markdown('### Welcome Admin ...')
                show_admin_page()            
            elif st.session_state['loggedIn']:  
                pass_id = login_df[login_df['UserName'] == st.session_state['username']]['Pass ID'].values[0]   
                name = pass_df[pass_df['Pass ID'] == pass_id]['Pass Name'].values[0]
                st.markdown(f'### Welcome {name} ...')
                show_main_page()  
            else:
                show_login_page()

    else:
        show_register_page()


# To hide streamlit default menu and footer
hide_streamlit_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            </style>
            """
st.markdown(hide_streamlit_style, unsafe_allow_html=True) 



