import numpy as np
from scipy.stats import t, f

#implementation uses numpy for basic matrix operations.
#Also uses scipy to determine the quantiles of the t and f distribution (could be done from scratch but is not the focus of the project, imo)
class OLSRegression:
    def __init__(self, X, y):
        self.X = np.hstack((np.ones((X.shape[0], 1)), X))  # Add intercept
        self.y = y
        self.n, self.p = self.X.shape
        self.beta_hat = None
        self.residuals = None
        self.sigma_squared = None
        self.var_beta = None #estimated variance of betahat
        self.fitted = False

    def fit(self):
        XtX_inv = np.linalg.inv(self.X.T @ self.X)
        self.beta_hat = XtX_inv @ self.X.T @ self.y
        self.residuals = self.y - self.X @ self.beta_hat
        self.sigma_squared = (self.residuals.T @ self.residuals) / (self.n - self.p)
        self.var_beta = self.sigma_squared * XtX_inv
        self.fitted = True

    def get_variance_matrix(self):
        if not self.fitted:
            raise ValueError("Model is not fitted")
        return self.var_beta

    def predict(self, X_new):
        if not self.fitted:
            raise ValueError("Model is jnot fitted.")
        X_new = np.hstack((np.ones((X_new.shape[0], 1)), X_new))
        return X_new @ self.beta_hat


class Tester:
    def __init__(self, ols: OLSRegression):
        if not ols.fitted:
            raise ValueError("OLS model must be fitted before testing.")
        self.ols = ols

    def confidence_intervals(self, alpha=0.05):
        var_beta = self.ols.get_variance_matrix()
        se_beta = np.sqrt(np.diag(var_beta))
        t_critical = t.ppf(1 - alpha / 2, self.ols.n - self.ols.p)
        lower_bounds = self.ols.beta_hat - t_critical * se_beta
        upper_bounds = self.ols.beta_hat + t_critical * se_beta
        return np.column_stack((lower_bounds, upper_bounds))

    def t_statistics(self, hypothesized_values=None): 
        if hypothesized_values is None:
            hypothesized_values = np.zeros_like(self.ols.beta_hat) # default: b_j = 0, for all j
        var_beta = self.ols.get_variance_matrix()
        se_beta = np.sqrt(np.diag(var_beta))
        return (self.ols.beta_hat - hypothesized_values) / se_beta


    def t_test(self, hypothesized_values=None, alpha=0.05):
        t_stats = self.t_statistics(hypothesized_values=hypothesized_values)
       
        p_values = 2 * (1 - t.cdf(np.abs(t_stats), df=self.ols.n - self.ols.p))
        # Evaluate significance
        significant = p_values < alpha
        return t_stats, p_values, significant


    def f_test(self, R, r):
        # F-test for H0: Rβ = r
        R_beta_hat = R @ self.ols.beta_hat - r
        cov_R_beta = R @ self.ols.get_variance_matrix() @ R.T
        F_stat = (R_beta_hat.T @ np.linalg.inv(cov_R_beta) @ R_beta_hat) / R.shape[0]
        F_stat /= self.ols.sigma_squared
        p_value = 1 - f.cdf(F_stat, R.shape[0], self.ols.n - self.ols.p)
        return F_stat, p_value

    def prediction_intervals(self, X_new, alpha=0.05):
        predictions = self.ols.predict(X_new)
        X_new = np.hstack((np.ones((X_new.shape[0], 1)), X_new))  
        XtX_inv = np.linalg.inv(self.ols.X.T @ self.ols.X)
        #h = np.array([x @ np.linalg.inv(self.ols.X.T @ self.ols.X) @ x.T for x in X_new])
        h = np.einsum('ij,jk,ik->i', X_new, XtX_inv, X_new)  # ChatGPT's optimization for the above line of code which is otherwise to slow
        t_critical = t.ppf(1 - alpha / 2, self.ols.n - self.ols.p)
        se_pred = np.sqrt(self.ols.sigma_squared * (1 + h))
        lower_bounds = predictions - t_critical * se_pred
        upper_bounds = predictions + t_critical * se_pred
        return predictions, lower_bounds, upper_bounds


def main():
    
    #can fix the np.seed to have consistent results
    X = np.random.rand(100, 2)  
    y = 3 + 2 * X[:, 0] + 4 * X[:, 1] + np.random.randn(100) * 0.5  # linear model with gaussian noise

    # Fit the OLS
    ols = OLSRegression(X, y)
    ols.fit()
    print("Beta coefficients:", ols.beta_hat)

    
    tester = Tester(ols)

    # Confidence intervals
    print("Confidence intervals:", tester.confidence_intervals())

    # t-tests
    t_stats, p_values, significant = tester.t_test()
    print("t-statistics:", t_stats)
    print("p-values:", p_values)
    print("Significant coefficients:", significant)

    # F-test
    R = np.eye(ols.p - 1, ols.p)  # Test all coefficients but intercept
    r = np.zeros(ols.p - 1)
    F_stat, F_p_value = tester.f_test(R, r)
    print("F-statistic:", F_stat)
    print("F-test p-value:", F_p_value)

    # Prediction intervals
    X_new = np.array([[0.5, 0.5], [0.2, 0.8]])
    predictions, lower_bounds, upper_bounds = tester.prediction_intervals(X_new)
    print("Predictions:", predictions)
    print("Prediction intervals:", np.column_stack((lower_bounds, upper_bounds)))

if __name__ == '__main__':
    main()
