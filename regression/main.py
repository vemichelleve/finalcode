import embedding
import model
import preprocess
from sklearn.model_selection import KFold


def avg(rms, mae):
    return (rms + mae) / 2


input_dataset = './Augmented_Feat.csv'
embedmodel = embedding.train_word2vec('./glove.6B.300d.txt')
question = './questions.csv'

df = preprocess.cleaning_dataset(input_dataset)
df = preprocess.question_demoting(df, question)

X, y, scaler_y = preprocess.scale(df)

X_train, X_test, y_train, y_test = preprocess.split(X, y, 0.2)

split = 5
index = 0
train_model = [None] * split
tokenizer = [None] * split
rms = [None] * split
mae = [None] * split
kfold = KFold(n_splits=split, shuffle=True, random_state=101)
for train, test in kfold.split(X_train, y_train):
    train_model[index], tokenizer[index] = model.train(X_train.iloc[train], y_train[train], embedmodel)
    test_results = model.predict(X_train.iloc[test], train_model[index], tokenizer[index])
    test_results, y_true = model.processresult(test_results, y_train[test], scaler_y)
    _, rms[index], mae[index] = model.evaluate(test_results, y_true)
    index += 1

index = 0
max = avg(rms[0], mae[0])
for i in range(1, split):
    if avg(rms[i], mae[i]) < max:
        index = i
        max = avg(rms[i], mae[i])

test_results = model.predict(X_test, train_model[index], tokenizer[index])
test_results, y_true = model.processresult(test_results, y_test, scaler_y)
pearson, rmse, maerror = model.evaluate(test_results, y_true)
print("Pearson", round(pearson, 4))
print("RMS", round(rmse, 4))
print("MAE", round(maerror, 4))
