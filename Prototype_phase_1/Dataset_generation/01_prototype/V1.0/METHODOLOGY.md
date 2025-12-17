# Methodology for Privacy-Preserving Synthetic Generation of Automotive Inventory Data

## 1. Introduction

This document delineates the methodology employed to generate synthetic datasets comprising physical and inventory characteristics of automotive parts. The primary objective is to facilitate research and algorithm development by producing realistic synthetic data that mitigates the risk of exposing confidential source information.

The source dataset contains sensitive measurements regarding part dimensions, weight, and inventory metrics within the automotive supply chain. To ensure confidentiality, the generation process relies exclusively on aggregate statistics and derived probabilistic rules, ensuring that no individual records or sensitive information are reproduced. This approach aligns with established frameworks for statistical disclosure control, where the goal is to enable valid statistical inference while protecting respondent privacy [1]. The methodology adopted here utilizes probabilistic sampling from marginal distributions combined with deterministic constraints to preserve physical realism [2, 3].

---

## 2. Data Extraction and Statistical Profiling

To facilitate the generation process, summary statistics were extracted from the confidential source dataset. This process involved the following distinct stages:

### 2.1. Unit Standardization
To ensure consistency, all dimensional measurements (length, width, depth) were converted to millimeters, and weight measurements were standardized to kilograms.

### 2.2. Descriptive Statistics
For every numeric variable—including dimensions, weight, quantity per box, inventory levels, and demand—descriptive statistics were computed. These included the mean, standard deviation, minimum, maximum, quantiles, and skewness. These aggregates serve as the foundation for the generative model, ensuring that the synthetic distributions closely approximate the original data [1].

### 2.3. Correlation Analysis
Pearson correlation coefficients were calculated between all numeric variables to capture linear dependencies. The resulting correlation matrix serves as a critical benchmark for validating the utility of the synthetic data [4].

### 2.4. Discretization and Conditional Profiling
To capture distributional variations more effectively than global statistics, the "Length" variable was discretized into bins. This follows the histogram-based generation approach described by Ping et al. [3], which allows for the preservation of non-linear distribution shapes. Within each bin, the 10th, 50th, and 90th percentiles for width, depth, and weight were computed. Bin counts were retained to enable probability-weighted sampling during generation.

### 2.5. Ratio-Based Constraints
In industrial and manufacturing contexts, data must adhere to physical laws and geometric logic. Mere statistical correlation is often insufficient to prevent the generation of physically impossible objects [5]. To address this, ratios between width/length (W/L), depth/width (D/W), and weight/volume (WT/Vol) were computed. Quantiles for these ratios were extracted to define deterministic bounds. This integration of constraints ensures that the generative model respects the physical relationships inherent in the data, a technique formalized in constraint-augmented synthetic data frameworks [2].

---

## 3. Synthetic Data Generation Framework

The generation of synthetic parts proceeds through a multi-step pipeline designed to balance statistical fidelity with physical plausibility:

1.  **Probabilistic Bin Selection**
    A length bin is selected based on the frequency distribution observed in the source dataset. The specific length value is then sampled uniformly within the bounds of the selected bin. This "independent attribute mode" of sampling from histograms is a standard method for preserving marginal distributions in privacy-preserving data synthesis [3].

2.  **Dimensional Sampling**
    Width, depth, and weight are sampled uniformly between the 10th and 90th percentiles calculated for the specific length bin. This conditional sampling approach maintains the local dependency between length and other physical attributes.

3.  **Constraint-Based Post-Processing**
    To prevent the generation of geometrically unrealistic parts, the sampled dimensions are subjected to ratio-based corrections.
    *   Width is clipped to remain within the plausible W/L ratio range.
    *   Depth is clipped to the plausible D/W ratio range.
    *   Weight is adjusted to fit the plausible weight-to-volume ratio.
    This step ensures that the synthetic data adheres to the "business rules" and physical constraints of the automotive domain [2, 5].

4.  **Inventory and Identification Variables**
    Operational metrics such as quantity per box, stock levels, and demand are sampled independently from their respective aggregate distributions. Unique identifiers (Item ID) are generated procedurally to distinguish synthetic entities.

---

## 4. Validation and Statistical Consistency

While the generator does not explicitly model a joint probability distribution (e.g., via a Gaussian Copula), the adherence to binning and ratio constraints implicitly preserves key relationships. The validation framework focuses on three pillars:

*   **Aggregate Comparison:** The mean, variance, and quantiles of the synthetic data are compared against the confidential source to ensure statistical similarity [1].
*   **Distributional Fidelity:** Histograms and boxplots are analyzed to verify that the synthetic data reproduces the shape and range of the original variables [1].
*   **Correlation and Constraint Verification:** The correlation matrix of the synthetic dataset is compared to the original matrix [4]. Furthermore, the ratios (W/L, D/W) are validated to ensure no physical anomalies exist, confirming the effectiveness of the constraint-based generation [2, 5].

---

## 5. Discussion

**Advantages**
The primary advantage of this methodology is the rigorous protection of privacy. By relying solely on summary statistics and binned distributions, the process prevents the "linkage" or reconstruction of specific confidential records [1]. Additionally, the use of explicit ratio constraints ensures that the data remains functionally useful for industrial applications, avoiding the common pitfall where synthetic data fails to meet domain-specific physical logic [5].

**Limitations**
The approach assumes that variables within bins are uniformly distributed, which may smooth out multimodal peaks present in the source data. Furthermore, because inventory metrics (demand, stock) are sampled independently, higher-order correlations between physical size and supply chain velocity are only captured if they are explicitly programmed as rules.

---

## 6. References

[1] J. P. Reiter, "Releasing Multiply-Imputed Synthetic Data Generated in Two Stages to Protect Confidentiality," *Journal of Official Statistics*, vol. 20, no. 4, pp. 579–602, 2004.

[2] N. Patki, R. Wedge, and K. Veeramachaneni, "The Synthetic Data Vault," in *IEEE International Conference on Data Science and Advanced Analytics (DSAA)*, 2016, pp. 399-410.

[3] H. Ping, J. Stoyanovich, and B. Howe, "DataSynthesizer: Privacy-Preserving Synthetic Datasets," in *Proceedings of the 29th International Conference on Scientific and Statistical Database Management (SSDBM)*, 2017.

[4] S. A. Assefa et al., "Generating Synthetic Data in Health Care: A Review," *Journal of Medical Internet Research*, vol. 22, no. 12, 2020.

[5] Y. Gao et al., "Artificial Intelligence-enabled smart manufacturing: A review," *Engineering*, vol. 6, no. 9, 2020.