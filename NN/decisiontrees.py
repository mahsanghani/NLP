import numpy as np
from collections import Counter

class DecisionTree:
    def __init__(self, max_depth=None):
        self.max_depth = max_depth
        self.tree = None

    def fit(self, X, y):
        self.tree = self._build_tree(X, y)

    def predict(self, X):
        return [self._predict(sample, self.tree) for sample in X]

    def _build_tree(self, X, y, depth=0):
        num_samples, num_features = X.shape
        unique_classes = np.unique(y)

        # If only one class remains or max depth is reached, return the class
        if len(unique_classes) == 1 or (self.max_depth and depth >= self.max_depth):
            return unique_classes[0]

        # Initialize best criteria
        best_feature, best_threshold = self._best_split(X, y)
        if best_feature is None:
            return Counter(y).most_common(1)[0][0]

        # Create the tree node
        left_indices = X[:, best_feature] <= best_threshold
        right_indices = X[:, best_feature] > best_threshold

        left_subtree = self._build_tree(X[left_indices], y[left_indices], depth + 1)
        right_subtree = self._build_tree(X[right_indices], y[right_indices], depth + 1)

        return {
            'feature_index': best_feature,
            'threshold': best_threshold,
            'left': left_subtree,
            'right': right_subtree
        }

    def _best_split(self, X, y):
        best_gain = -1
        best_feature, best_threshold = None, None

        for feature_index in range(X.shape[1]):
            thresholds = np.unique(X[:, feature_index])
            for threshold in thresholds:
                gain = self._information_gain(X, y, feature_index, threshold)
                if gain > best_gain:
                    best_gain = gain
                    best_feature = feature_index
                    best_threshold = threshold

        return best_feature, best_threshold

    def _information_gain(self, X, y, feature_index, threshold):
        parent_entropy = self._entropy(y)

        left_indices = X[:, feature_index] <= threshold
        right_indices = X[:, feature_index] > threshold

        if len(y[left_indices]) == 0 or len(y[right_indices]) == 0:
            return 0

        n = len(y)
        n_left, n_right = len(y[left_indices]), len(y[right_indices])
        child_entropy = (n_left / n) * self._entropy(y[left_indices]) + (n_right / n) * self._entropy(y[right_indices])

        return parent_entropy - child_entropy

    def _entropy(self, y):
        if len(y) == 0:
            return 0

        class_counts = Counter(y)
        probabilities = [count / len(y) for count in class_counts.values()]
        return -sum(p * np.log2(p) for p in probabilities if p > 0)

    def _predict(self, sample, tree):
        if not isinstance(tree, dict):
            return tree

        feature_value = sample[tree['feature_index']]
        if feature_value <= tree['threshold']:
            return self._predict(sample, tree['left'])
        else:
            return self._predict(sample, tree['right'])

# Example Usage
if __name__ == "__main__":
    # Sample dataset
    X = np.array([[2, 3], [1, 1], [4, 5], [4, 4], [2, 1], [1, 3], [3, 3], [3, 1]])
    y = np.array([0, 0, 1, 1, 0, 0, 1, 1])

    # Create and train the decision tree
    clf = DecisionTree(max_depth=3)
    clf.fit(X, y)

    # Make predictions
    predictions = clf.predict(X)
    print("Predictions:", predictions)
