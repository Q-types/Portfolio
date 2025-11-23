# Bank Note Authentication Using Deep Neural Networks

Deep Learning project demonstrating binary classification for counterfeit detection using TensorFlow and Keras.

## 🎯 Project Overview

This project applies **Deep Neural Networks (DNN)** to the problem of bank note authentication, distinguishing between genuine and forged currency using wavelet-transformed image features. The model achieves **97% accuracy** on test data, demonstrating the effectiveness of deep learning for financial fraud detection.

### Business Context

Counterfeit currency detection is a critical challenge for financial institutions and law enforcement. Traditional methods rely on manual inspection or specialized equipment, which can be:
- Time-consuming and expensive
- Inconsistent across different operators
- Difficult to scale for high-volume processing

This project showcases how **machine learning can automate and standardize** the authentication process with high accuracy.

---

## 📊 Dataset

**Source:** UCI Machine Learning Repository - Bank Note Authentication Dataset

The dataset contains **1,372 records** with wavelet-transformed features extracted from genuine and forged bank note images.

### Features
- **Image.Var** - Variance of Wavelet Transformed image (continuous)
- **Image.Skew** - Skewness of Wavelet Transformed image (continuous)
- **Image.Curt** - Kurtosis of Wavelet Transformed image (continuous)
- **Entropy** - Entropy of image (continuous)
- **Class** - Target variable (0 = Fake, 1 = Authentic)

### Data Split
- **Training set:** 70% (961 samples)
- **Validation set:** 21% (289 samples, from training data)
- **Test set:** 30% (411 samples)

---

## 🏗️ Model Architecture

### Neural Network Structure

```
Input Layer:  4 neurons (matching 4 input features)
              ↓
Hidden Layer: 8 neurons with ReLU activation
              ↓
Hidden Layer: 8 neurons with ReLU activation
              ↓
Output Layer: 1 neuron with Sigmoid activation (binary classification)
```

### Configuration
- **Optimizer:** Adam (adaptive learning rate optimization)
- **Loss Function:** Binary Crossentropy
- **Metrics:** Accuracy
- **Training Epochs:** 600
- **Validation Split:** 30%

### Feature Scaling
- **Method:** MinMaxScaler (scales features to [0, 1] range)
- **Rationale:** Neural networks converge faster with normalized inputs

---

## 📈 Performance Results

### Deep Neural Network

| Metric | Fake (Class 0) | Authentic (Class 1) | Overall |
|--------|----------------|---------------------|---------|
| **Precision** | 0.96 | 0.99 | - |
| **Recall** | 0.99 | 0.95 | - |
| **F1-Score** | 0.97 | 0.97 | **0.97** |
| **Accuracy** | - | - | **97%** |

### Confusion Matrix (Test Set)
```
                Predicted
             Fake  Authentic
Actual Fake   215      0
   Authentic    3    197
```

**Interpretation:**
- **False Positives:** 0 (no authentic notes misclassified as fake)
- **False Negatives:** 3 (3 fake notes misclassified as authentic)
- The model is slightly conservative, erring on the side of accepting potentially fake notes rather than rejecting genuine ones

### Baseline Comparison: Random Forest

For validation, a **Random Forest classifier** (200 estimators) was trained on the same dataset:

| Metric | Random Forest | DNN |
|--------|---------------|-----|
| **Accuracy** | 99% | 97% |
| **Precision (Avg)** | 0.99 | 0.97 |

**Key Finding:** Both models achieve excellent performance, demonstrating that this is a well-defined classification problem. The DNN provides comparable results with the advantage of being scalable to more complex feature representations (e.g., raw images).

---

## 🚀 Technical Implementation

### Libraries & Frameworks
- **TensorFlow / Keras** - Deep learning framework
- **scikit-learn** - Data preprocessing, model evaluation
- **pandas** - Data manipulation
- **NumPy** - Numerical operations
- **Matplotlib / Seaborn** - Visualization

### Key Techniques
1. **Exploratory Data Analysis**
   - Pairplot visualization to identify feature separability
   - Class distribution analysis

2. **Data Preprocessing**
   - Train-test split (70/30)
   - MinMaxScaler normalization

3. **Model Training**
   - Sequential neural network with 2 hidden layers
   - Adam optimizer with automatic learning rate adaptation
   - Validation monitoring to detect overfitting

4. **Evaluation**
   - Classification report (precision, recall, F1-score)
   - Confusion matrix visualization
   - Training history plots (loss & accuracy curves)

---

## 💻 Usage

### Prerequisites
```bash
pip install -r requirements.txt
```

### Running the Notebook
```bash
jupyter notebook bank_note_authentication.ipynb
```

The notebook provides:
- Step-by-step walkthrough with markdown explanations
- Visualization of training progress
- Model evaluation metrics
- Comparison with Random Forest baseline

---

## 📁 Project Structure

```
Bank_Note_Authentication_DNN/
├── README.md                          # This file
├── bank_note_authentication.ipynb     # Main Jupyter notebook
├── bank_note_data.csv                 # UCI dataset
├── requirements.txt                   # Python dependencies
├── LICENSE                            # MIT License
└── .gitignore                         # Git ignore rules
```

---

## 🎓 Learning Outcomes

This project demonstrates proficiency in:

✅ **Deep Learning Fundamentals**
- Neural network architecture design
- Activation function selection (ReLU, Sigmoid)
- Loss function and optimizer configuration

✅ **TensorFlow / Keras Framework**
- Sequential model API
- Layer configuration
- Training and evaluation workflows

✅ **Machine Learning Best Practices**
- Train-validation-test split
- Feature scaling for neural networks
- Model evaluation with multiple metrics

✅ **Data Science Workflow**
- EDA with visualization
- Baseline model comparison
- Performance interpretation

---

## 🔮 Future Enhancements

Potential extensions to explore:

1. **Hyperparameter Tuning**
   - Experiment with different architectures (layer count, neuron count)
   - Learning rate optimization
   - Dropout layers for regularization

2. **Advanced Architectures**
   - Convolutional Neural Networks (if using raw images)
   - Ensemble methods combining DNN with Random Forest

3. **Model Deployment**
   - Convert to TensorFlow Lite for mobile deployment
   - Create REST API for real-time authentication
   - Build web interface for batch processing

4. **Explainability**
   - Feature importance analysis
   - SHAP values to understand model decisions
   - Visualization of learned representations

---

## 📝 License

MIT License

---

**Author:** Q-types  
**Domain:** Financial Fraud Detection / Deep Learning  
**Dataset Source:** [UCI Machine Learning Repository](https://archive.ics.uci.edu/ml/datasets/banknote+authentication)
