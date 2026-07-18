---

title: "Machine Learning: MNIST Digit Classification"

date: 2026-07-18

draft: false

slug: "mnist-digit-classification"

---

Compared 6 classification models — from Logistic Regression to CNNs — for predicting handwritten digits from the MNIST dataset, benchmarking accuracy, speed, and where each model breaks down.

<!--more-->

This project tackles the classic MNIST handwritten digit dataset, comparing six models across two categories: traditional machine learning (Logistic Regression, LDA, SVM, Decision Tree) and CNNs (LeNet, a Sequential CNN built with Keras).



Each model was evaluated on precision, recall, and F1 score, alongside run time, to weigh accuracy against computational cost.



![Confusion matrix heatmaps for all six models](confusionmatrix.png)

Confusion matrices for Logistic Regression, LDA, SVM, Decision Tree, LeNet, and Sequential CNN



LeNet came out on top — 0.99 F1 score, and notably 3x faster than the Sequential CNN for near-identical accuracy. This makes sense given LeNet was purpose-built for digit recognition. The simpler models (Logistic Regression, LDA, Decision Tree) traded some accuracy for speed, with Logistic Regression the strongest of that group at 0.92 F1. SVM stood out as the weakest performer overall — high computational cost for comparatively unremarkable accuracy, likely due to MNIST's high dimensionality (784 features per image).



Digging deeper into where LeNet actually fails, I looked at specific misclassified digit pairs:



![Pixel heatmaps showing misclassifications between 4/9 and 5/3](pixelheatmaps.png)

Pixel heatmaps of LeNet's most common errors: 4↔9 and 5↔3 confusion



The only two digit pairs LeNet confused more than 10 times were 4→9 and 5→3. Every model tested predicted 0s and 1s near-perfectly, likely due to their visually distinct shapes compared to other digits.



# Downloads



## Downloads

<a href="/files/numbermnist.ipynb" download>📓 Download the Notebook (.ipynb)</a><br>
<a href="/files/numbermnist.pdf" download>📄 Download the Full Report (.pdf)</a>
