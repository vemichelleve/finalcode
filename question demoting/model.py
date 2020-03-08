import pandas as pd
from keras.models import load_model
from scipy.stats import pearsonr
from sklearn.metrics import mean_squared_error, mean_absolute_error
from math import sqrt

import lstm
import embedding

# initialized required parameters for LSTM network...
EMBEDDING_DIM = 300
MAX_SEQUENCE_LENGTH = 5
VALIDATION_SPLIT = 0.20
RATE_DROP_LSTM = 0.20
RATE_DROP_DENSE = 0.50
NUMBER_LSTM = 500
NUMBER_DENSE_UNITS = 50
ACTIVATION_FUNCTION = 'sigmoid'


def train(df, y, model):
    df['Ref Answer'] = df['Ref Answer'].astype(str)
    df['Answer'] = df['Answer'].astype(str)

    answer1 = df['Ref Answer'].tolist()
    answer2 = df['Answer'].tolist()
    scores = y.tolist()

    ## creating answers pairs
    answers_pair = [(x1, x2) for x1, x2 in zip(answer1, answer2)]
    print("----------created answers pairs-----------")

    ## add features for feature engineering
    feat = pd.DataFrame(
        df[['Length Answer', 'Length Ref Answer', 'Len Ref By Ans', 'Words Answer', 'Unique Words Answer']])

    # creating word embedding meta data for word embedding
    tokenizer, embedding_matrix = embedding.word_embed_meta_data(answer1 + answer2, EMBEDDING_DIM, model)
    embedding_meta_data = {'tokenizer': tokenizer, 'embedding_matrix': embedding_matrix}
    print("----------created word embedding meta data-----------")

    # SiameneBiLSTM is a class for  Long short Term Memory networks
    siamese = lstm.SiameneLSTM(EMBEDDING_DIM, MAX_SEQUENCE_LENGTH, NUMBER_LSTM, NUMBER_DENSE_UNITS,
                               RATE_DROP_LSTM, RATE_DROP_DENSE, ACTIVATION_FUNCTION, VALIDATION_SPLIT)
    model_path = siamese.train_model(answers_pair, feat, scores, embedding_meta_data, model_save_directory='./')
    # preds, model_path = siamese.train_model(answers_pair, scores, embedding_meta_data, model_save_directory='./')

    # load the train data in model...
    model = load_model(model_path)
    print("----------model trained-----------")
    return model, tokenizer


def predict(df_test, model, tokenizer):
    df_test['Ref Answer'] = df_test['Ref Answer'].astype(str)
    df_test['Answer'] = df_test['Answer'].astype(str)

    answer1_test = df_test['Ref Answer'].tolist()
    answer2_test = df_test['Answer'].tolist()

    ## creating answers pairs
    answers_test_pair = [(x1, x2) for x1, x2 in zip(answer1_test, answer2_test)]
    print("----------created test dataset-----------")

    ## features input
    feat = pd.DataFrame(
        df_test[['Length Answer', 'Length Ref Answer', 'Len Ref By Ans', 'Words Answer', 'Unique Words Answer']])

    test_data_x1, test_data_x2, feat, leaks_test = embedding.create_test_data(tokenizer, answers_test_pair, feat,
                                                                              MAX_SEQUENCE_LENGTH)

    # predict the results
    preds = list(model.predict([test_data_x1, test_data_x2, feat, leaks_test], verbose=1).ravel())
    print("----------predicted test results-----------")

    # mapping results with input test data...

    return preds


def processresult(test_results, y_test, scaler_y):
    ## Processing of the test result to obtain a uniform format and then inverse transform
    y_true = y_test.tolist()
    y_true = scaler_y.inverse_transform(y_true)
    y_t = []
    for i in range(len(y_true)):
        for x in y_true[i]:
            y_t.append(x)
    y_true = y_t

    t = []
    for i in range(len(test_results)):
        temp = []
        temp.append(test_results[i])
        t.append(temp)
    test_results = t
    test_results = pd.DataFrame(test_results)
    test_results = scaler_y.inverse_transform(test_results)
    t = []
    for i in range(len(test_results)):
        for x in test_results[i]:
            t.append(x)
    test_results = t

    return test_results, y_true


def evaluate(test_results, y_true):
    print('test results')
    print(test_results)
    print('y_true')
    print(y_true)

    pearson, pval = pearsonr(test_results, y_true)
    rms = sqrt(mean_squared_error(test_results, y_true))
    mae = mean_absolute_error(test_results, y_true)

    return pearson, rms, mae
