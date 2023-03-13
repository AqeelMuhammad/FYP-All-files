from flask import *
import json, time
from read_data import *
from feature_extraction import *
from noise_reduction import *
from peak_detection import *
# from sklearn.linear_model import LinearRegression
# from sklearn.preprocessing import MinMaxScaler

app = Flask(__name__)

@app.route("/", methods = ['GET'])
def home_page():
    data_set = {'Page':'Home', 'Message':'Connected', 'Timestamp':time.time()}
    json_dump = json.dumps(data_set)

    return json_dump

@app.route("/is/stressed/", methods = ['POST'])
def check_stressed():
    user_query = str(request.args.get('user')) # /user/?user=UserName
    data = json.loads(request.data.decode())
    ppg = data['ppg']
    clr = data['clr']
    dev = data['device']
    # print(ppg)
    result = is_stressed(ppg, clr, dev)
    # print(result)
    data_set = {'User': f'{user_query}', 'stressed':int(result[0]),'HR mean':result[1], 'Timestamp':time.time()}
    json_dump = json.dumps(data_set)

    return json_dump

if __name__ == '__main__':
    app.run(port=7777)
