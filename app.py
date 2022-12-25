#render template renders html from render folder
from flask import Flask,render_template,request
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import nltk, os, sys, json
import requests,re
from textblob import Word
from transformers import pipeline
import requests
import random
#pyinstaller C:\Users\Administrator\Documents\Work\KUET-chatbot\KUETBOT\app.py --add-data "C:\Users\Administrator\Documents\Work\KUET-chatbot\KUETBOT\templates;templates" --add-data "C:\Users\Administrator\Documents\Work\KUET-chatbot\KUETBOT\static;static"

#new instance of flask
if getattr(sys, 'frozen', False):
    # we are running in a bundle, base folder in executable is sys._MEIPASS
    bundle_dir = sys._MEIPASS
    template_folder = bundle_dir + '/templates'
    static_folder = bundle_dir + '/static'
    app = Flask(__name__, template_folder=template_folder, static_folder=static_folder)
else:
    # we are running in a normal Python environment
    bundle_dir = os.path.dirname(os.path.abspath(__file__))
    app = Flask(__name__)


#global variable list
sentenceList = nltk.sent_tokenize("demo")
fullText="demo"
stopWords="demo"
sentenceListFirstLine = ["demo"]


#app.route gives the webpage where this functioni will be [triggered],
#in this case, "/" or home page
#if a route has post or get forms, needs to be defined
@app.route("/", methods=['GET','POST'])
def hello_world():
    app.debug = True
    return render_template('home.html')

### GO TO SPECIFIC PROJECT PAGES ###

@app.route("/chatbot")
def Chatbot():
  sentenceUpdate()
  return render_template('chatbot.html')

@app.route("/summarization")
def Summarization():
  return render_template('summarization.html')



### TEXT SUMMARIZATION SPECIFIC CODE ### 

@app.route("/summarize",methods=['GET', 'POST'])
def Summarize():
    inp_txt = ""
    out_txt = ""
    if request.method == 'POST':
        inp_txt = request.form['content']
        out_txt = "The input was : "
        out_txt=Summarization_out(inp_txt)
    return render_template("summarization.html",out_txt=out_txt)

def summary_return(dat,summarizer):
  summary = summarizer(dat)[0]["summary_text"]
  return summary
def Summarization_out(inp_txt):
    hub_model_id = r"C:\Users\Inception\Desktop\python project dev\KUET-Everything\model"
    print("ok6")
    summarizer = pipeline("summarization", model=hub_model_id)
    ans=summary_return(inp_txt,summarizer)
    return ans

### ERROR CORRECTION SPECIFIC CODE ###

@app.route('/error', methods=['GET', 'POST'])
def auto_correction():
    inp_txt = ""
    out_txt = ""
    if request.method == 'POST':
        inp_txt = request.form['content']
        out_txt = "The input was : "
        print(inp_txt)
        print("ok1")
        out_txt=error_correct(inp_txt)
        print("ok2")
    return render_template("error.html",out_txt=out_txt)
    
API_URL = "https://api-inference.huggingface.co/models/shahidul034/error_correction_Bangla_keyboard_typing2"
headers = {"Authorization": "Bearer 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"}

def query(payload):
	response = requests.post(API_URL, headers=headers, json=payload)
	return response.json()
	
def error_correct(inputs):
	output = query({"inputs":inputs})
	return output[0]['generated_text'][:len(inputs)]


### KUET CHATBOT SPECIFIC CODE ###

#this is called by javascript to get response
@app.route("/botResponse/<userText>", methods=['GET','POST'])
def botResponse(userText):
    bot_response=''
    #at first only match the first lines for more accurate search, due to the nature of the dataset
    firstLineFlag,matchIndex=checkBlocks(userText)
    if firstLineFlag==1:
        bot_response=bot_response+sentenceList[matchIndex]
        flag,out=searching(bot_response,fullText)
        return out
    else:  
        sentenceList.append(userText)
        cm=CountVectorizer(stop_words=stopWords).fit_transform(sentenceList)
        similarity_scores=cosine_similarity(cm[-1],cm)
        similarity_scores_list=similarity_scores.flatten()
        index=index_sort(similarity_scores_list)
        index=index[1:]
        response_flag=0
        j=0
        for i in range(len(index)):
            if similarity_scores_list[index[i]]>0.0:
                bot_response=bot_response+sentenceList[index[i]]
                response_flag=1
                j+=1
            if j>1:
                break
        if response_flag==0:
            bot_response = BasicConversation(userText)
        else:
            flag,out=searching(bot_response,fullText)
            if flag:
                bot_response=out
            else:
                botResponse = RemoveBlock(botResponse)
        sentenceList.remove(userText)
        return bot_response    

def BasicConversation(userInput):
    convoList = ["hello hi hey good morning good evening","bye goodbye goodnight"]
    greetingsReplyList = ["Hey! I am KUETBOT and I am here to give you any information related to KUET.",
    "Hello! Ask me anything about KUET and I will try to give you an answer.",
    "Hi! Hope you're having a good day! Ask me anything about KUET."]
    byeReplyList = ["I hope I was helpful for your querries, see you soon!",
    "Have a good day and come back anytime!",
    "If you need more information about KUET, come back anytime!"]
    convoList.append(userInput)
    cm=CountVectorizer().fit_transform(convoList)
    tempInputVector = cm[-1]
    cm = cm[:-1,:]
    similarity_scores=cosine_similarity(tempInputVector,cm)
    similarity_scores_list=similarity_scores.flatten()
    index=index_sort(similarity_scores_list)
    convoList.pop()
    if similarity_scores_list[index[0]]>0.0:
        if(index[0] == 0):
            return random.choice(greetingsReplyList)
        elif(index[0] == 1):
            return random.choice(byeReplyList)
    else:
        return "I apologize, I don't understand."


#Updates sentence main sentence list
def sentenceUpdate():
    global fullText
    global stopWords
    global sentenceList
    global sentenceListFirstLine
    sentenceListFirstLine.clear()
    
    url= r'https://raw.githubusercontent.com/shahidul034/KUET-everything/main/static/Software-Project-Data.txt'
    page = requests.get(url)
    fullText = page.text

    url= r'https://raw.githubusercontent.com/shahidul034/KUET-everything/main/static/StopWords.txt'
    page = requests.get(url)
    stopWords = page.text.split()
    # fullText = open(r"C:\\Users\Administrator\Documents\Work\KUET-everything\static\Software-Project-Data.txt",encoding="utf8").read()
    # stopWords = open(r"C:\\Users\Administrator\Documents\Work\KUET-everything\static\StopWords.txt",encoding="utf8").read().split()
    sentenceList = fullText.split("||")
    for block in sentenceList:
        sentenceListFirstLine.append(block.split('\n')[0])


#sorting method for sorting result quality
def index_sort(list_var):
  length=len(list_var)
  list_index=list(range(0,length))
  x=list_var
  for i in range(length):
    for j in range(length):
      if x[list_index[i]] > x[list_index[j]]:
        temp=list_index[i]
        list_index[i]=list_index[j]
        list_index[j]=temp
  return list_index

#searches all the firstlines for to match first
def checkBlocks(input):
    global sentenceListFirstLine
    sentenceListFirstLine.append(input)
    #creates word vector
    cm=CountVectorizer().fit_transform(sentenceListFirstLine)
    tempInputVector = cm[-1]
    #used slicing to remove input text vector to avoid full match duplication
    cm = cm[:-1,:]
    #find similarity using cosine distance
    similarity_scores=cosine_similarity(tempInputVector,cm)
    similarity_scores_list=similarity_scores.flatten()
    index=index_sort(similarity_scores_list)
    sentenceListFirstLine.pop()
    if similarity_scores_list[index[0]]>0.0:
        print(sentenceListFirstLine[index[0]],file=sys.stderr)
        return 1,index[0]
    else:
        return 0,0


#Checks for complete Regular expression blocks
def searching(botResponse,fullText):
    #search for occurence of block start
    search1=re.search("//.*//", botResponse)
    if search1:
        print("start block found",file=sys.stderr)
        ans=search1.group()
        ans= ans.replace("//","")
        #search_string="//"+ans+"//"+"(.*\n)*"+"\[\["+ans+"\]\]"
        search_string = '(//'+ans+'//)(.+)((?:\n.+)*)(\[\['+ans+'\]\])'
        #search for entire block in the found answer, if exists, ignore blocks and return already found result
        search=re.search(search_string,botResponse,re.MULTILINE)
        if search:
            #an entire block exists in the already found result, no need to shorten it
            return 1,RemoveBlock(botResponse)
        else:
            #only starting of a block is found, search for whole block including block end in the fulltext and return
            search2 = re.search(search_string,fullText,re.MULTILINE)
            if search2:
                #print("whole block found",file=sys.stderr)
                msg=search2.group()
                msg = RemoveBlock(msg)
                return 1,msg
            else:
                #print("start block found but whole block not found",file=sys.stderr)
                return 0,"" 
    else:
        #print("start block not found",file=sys.stderr)
        #start block not found, replacing end block if exists
        botResponse=RemoveBlock(botResponse)
        return 1,botResponse

def RemoveBlock(msg):
    msg=re.sub("//.*//","",msg)
    msg=re.sub("\[\[.*\]\]","",msg)
    msg=re.sub("\|\|","",msg)
    return msg

def conversation(input):
    API_URL = "https://api-inference.huggingface.co/models/microsoft/DialoGPT-large"
    headers = {"Authorization": "Bearer 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"}

    def query(payload):
        response = requests.post(API_URL, headers=headers, json=payload)
        return response.json()
        
    output = query({
        "inputs": {
            "text": input
        },
    })
    return output['generated_text']

if __name__ == "__main__":
    app.run(debug=True)
