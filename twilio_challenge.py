import streamlit as st
import random
from PIL import Image
import time
import base64
import boto3
import json
import os
import requests
from twilio.rest import Client
import datetime 

# Generative AI Libraries
import google.generativeai as genai


image = Image.open('media/twilio_challenge.png')
st.sidebar.image(image, caption="Challenge Twilio App", width=256)
app_mode = st.sidebar.selectbox("Choose app mode", ["Run App", "About Me"])

output_dir = "gen_images"
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

# Twilio Set Up
account_sid = st.secrets['twilio']['account_sid']
auth_token = st.secrets['twilio']['auth_token']
to_whatsapp_number = st.secrets['twilio']['phone_number']
service_id = st.secrets['twilio']['service_number']
client = Client(account_sid, auth_token)

# Github Set Up
token = st.secrets['github']['token']
username = st.secrets['github']['username']
repo = st.secrets['github']['repo']
path = st.secrets['github']['path']

# Generative AI models
genai.configure(api_key=st.secrets['gemini']['api_gem_key'])
model = genai.GenerativeModel(model_name="gemini-1.5-flash")

bedrock = boto3.client(
    service_name='bedrock-runtime',
    aws_access_key_id = st.secrets['aws']['AWS_ACCESS_KEY'],
    aws_secret_access_key = st.secrets['aws']['AWS_SECRET_KEY'],
    region_name='us-east-1'
)
model_id = "stability.stable-diffusion-xl-v1"


# Función para enviar OTP
def send_otp(phone_number,service_id):
   
   verification = client.verify \
       .v2 \
       .services(service_id) \
       .verifications \
       .create(to=phone_number, channel='sms')

   return verification.sid

def verify_otp(phone_number, service_id,input_otp):

   verification_check = client.verify \
       .v2 \
       .services(service_id) \
       .verification_checks \
       .create(to=phone_number, code=input_otp)
   
   print(verification_check.status)
   
   
   return verification_check.status
   
# Session States
if 'otp_sent' not in st.session_state:
    st.session_state.otp_sent = False
if 'generated_otp' not in st.session_state:
    st.session_state.generated_otp = None
if 'phone_number' not in st.session_state:
    st.session_state.phone_number = None
if 'otp_verified' not in st.session_state:
    st.session_state.otp_verified = False
if 'tweet_gen' not in st.session_state:
    st.session_state.tweet_gen = False
if 'prompt' not in st.session_state:
    st.session_state.prompt = None



if not st.session_state.otp_verified:
    if not st.session_state.otp_sent:

        st.title("Welcome to the Twilio Challenge using AI")
        st.subheader('🤔 But First, Are You a Real Person? 🧐')
        st.caption("OTP Verification with Twilio")
        phone_number = st.text_input('Enter your phone number (with country code)', '+57')
        st.session_state.phone_number = phone_number

        if st.button('Send OTP'):
        
            st.session_state.generated_otp = send_otp(to_whatsapp_number,service_id)
            print(f"el codigo generado fue {st.session_state.generated_otp}")
            st.success(f'OTP Send successfully for {st.session_state.phone_number}! ')
            st.session_state.otp_sent = True

            if st.button("Let's To Verify"):
                print('OK')
            
    else:

        st.title("Welcome to the Twilio Challenge Gen AI App")
        st.subheader('🤔 But First, Are You a Real Person? 🧐')
        st.caption("OTP Verification with Twilio")

        
        
        
        input_otp = st.text_input('Enter the OTP you received', '')

        if st.button('Verify OTP'):
            if verify_otp(to_whatsapp_number, service_id, input_otp):
                st.success(f'OTP verified successfully for {st.session_state.phone_number}!')
                st.session_state.otp_verified = True

                st.subheader('Great Job! Now Enjoy the App 💪🏻')

                if st.button('Go To the App 🚀'):
                    print('OK')
            else:
                st.error('Invalid OTP. Please try again.')
else:


    if app_mode == 'Run App':
        st.title("Welcome To Twilio Tweet Magic App")
        st.success(" Generate and share tweets with emotion and images. Powered by Twilio.👇 ")

        c1,c2,c3,c4 = st.columns((15,8,10,1))
        feelings = ['Happiness','Sorprise','Excitement','Pride','Hope','Sarcasm','Confusion','Inspiration','Worry']
        paste_url = c1.text_input('Url',label_visibility='visible',placeholder="Paste Your URL Here 👈🏻")
        choose_feeling =  c2.selectbox("Choose Feeling", feelings)
        today = datetime.date.today()
        c3.metric(label="Date", value=str(today))

        if c1.button('Generate Tweet'):
            
        
            prompt = f"From this {paste_url} article , Can you craft a {choose_feeling} Tweet summarizing this for maximum social media impact? , Please I only want the Tweet I don't need the explanations"
            response = model.generate_content(prompt)

            progress_text = "Generating Tweet . Please wait ⏳"
            my_bar = st.progress(0, text=progress_text)

            for percent_complete in range(100):
                time.sleep(0.03)  # Esperar 0.03 segundos en cada iteración
                my_bar.progress(percent_complete + 1, text=progress_text)

            st.subheader('Here Your Tweet 👇🏻', divider='rainbow')
            st.markdown(response.parts[0].text)

            # Save Prompt Image in st.session_state
            prompt_bedrock = prompt = f"Can you build a realistic image in a futuristic style that captures the dominant {choose_feeling} emotion in this text ? '{response.parts[0].text}' ?"
            st.session_state.new_image_prompt = prompt_bedrock
            st.session_state.tweet_gen = True
            
        if 'new_image_prompt' in st.session_state:

            if c2.button('Generate Image'):

                image_prompt = st.session_state.new_image_prompt #
                seed = random.randint(0, 4294967295)
                native_request = {
                    "text_prompts": [{"text": image_prompt}],
                    "style_preset": "photographic",
                    "seed": seed,
                    "cfg_scale": 10,
                    "steps": 30,
                }

                request = json.dumps(native_request)

                # Invoke the model with the request.
                response = bedrock.invoke_model(modelId=model_id, body=request)


                progress_text_image = "The App is generating your image . Please wait ⏳"
                my_bar = st.progress(0, text=progress_text_image)

                for percent_complete in range(100):
                    time.sleep(0.03)  
                    my_bar.progress(percent_complete + 1, text=progress_text_image)

                # Decode the response body.
                model_response = json.loads(response["body"].read())

                # Extract the image data.
                base64_image_data = model_response["artifacts"][0]["base64"]

                image_data = base64.b64decode(base64_image_data)
                image_name = f"tweet_image_gen_{response['ResponseMetadata']['RequestId'].split('-')[0]}.png"

                image_path = os.path.join(output_dir, image_name)
                with open(image_path, "wb") as file:
                    file.write(image_data)
                
                # Github Upload
                with open(image_path, 'rb') as img_file:
                    img_data = img_file.read()
                    img_base64 = base64.b64encode(img_data).decode('utf-8')
                
                path_git = f'gen_images/{image_name}'
                url = f'https://api.github.com/repos/{username}/{repo}/contents/{path_git}'

                # Request
                data = {
                    'message': 'Add AI generated image',
                    'content': img_base64,
                    'branch': 'main'
                }

                headers = {
                    'Authorization': f'token {token}',
                    'Accept': 'application/vnd.github.v3+json'
                }

                # Hacer la solicitud
                response = requests.put(url, json=data, headers=headers)

                if response.status_code == 201:
                    print('Image Upload Success To GitHub')
                else:
                    print(f'Error Uploading Image: {response.status_code}')
                    print(response.json())

                
                st.subheader('👈🏻 Here Your Image  &  Tweet 👇🏻 ', divider='rainbow')
                st.markdown(st.session_state.new_image_prompt)
                image_gen = Image.open(image_path)
                st.sidebar.image(image_gen, caption="Image Generated", width=256)


                # Save Prompt To Send to Wsp in st.session_state
                st.session_state.previous_tweet_prompt = st.session_state.new_image_prompt
                st.session_state.image_name = path_git
                st.session_state.image_gen = True


        if 'previous_tweet_prompt' in st.session_state:
            if c3.button('Send Tweet & Image'):
                
                # Send Message
                message = client.messages \
                                .create(
                                    body=f"*Tweet: 👇🏻* \n\n {st.session_state.previous_tweet_prompt}",
                                    from_='whatsapp:+14155238886',
                                    to=f'whatsapp:{to_whatsapp_number}'
                                )
                
                st.subheader('🧐 Check Your Phone , Share Your Tweet 🚀 ', divider='rainbow')
                st.success(f"Message {message.sid} sent succesfully")
                

                if 'image_name' in st.session_state:
                    # Send Images
                    path_git_final = st.session_state.image_name
                    print(path_git_final)
                    url_image = f'https://raw.githubusercontent.com/{username}/{repo}/main/{path_git_final}'
                    message_img = client.messages \
                                    .create(
                                        body="Finally Here's an image for you! 👆🏻",  # Optional message text
                                        media_url=[url_image] ,
                                        from_='whatsapp:+14155238886',
                                        to=f'whatsapp:{to_whatsapp_number}'
                                    )
                    
                    
                    st.success(f"Image {message_img.sid} sent succesfully")

    elif app_mode == "About Me":
        st.title('Challenge Twilio App')
        st.success("Feel free to contacting me here 👇 ")



        col1, col2, col3, col4 = st.columns((2, 1, 2, 1))
        
        col1.page_link("https://datexland.medium.com/", label="**Blog**", icon="🗒️")
        col1.page_link("https://alexbonella.github.io/", label="**Website**", icon="🌎")
        col1.page_link("https://www.linkedin.com/in/alexanderbolano/", label="**LinkedIn**", icon="📌")
        col1.page_link("https://twitter.com/datexland", label="**X**", icon="📝")

        image2 = Image.open('media/profile_ai.jpeg')
        col3.image(image2, width=230)   