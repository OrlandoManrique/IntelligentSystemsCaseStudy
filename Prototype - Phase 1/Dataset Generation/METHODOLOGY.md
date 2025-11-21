# Synthetic Part Data Generation

## 1. Overview

This document describes the methodology used to generate synthetic datasets of parts with physical and inventory characteristics. The goal is to produce realistic synthetic data for research and algorithm development without exposing confidential source data.

The confidential dataset includes measurements of part dimensions, weight, and inventory metrics. Only aggregate statistics and derived rules are used for synthetic data generation, ensuring that no sensitive information is reproduced.

Synthetic data generation for tabular and industrial datasets has been widely discussed in the literature, with approaches relying on probabilistic sampling from marginal distributions and enforcing simple ratio constraints to preserve realistic relationships between variables [1,2,3].

---

## 2. Data Extraction from Confidential Dataset

From the confidential dataset, the following steps were performed to extract summary statistics for generation:

1. **Unit conversion**  
   - Length, width, and depth converted from inches to centimeters.  
   - Weight converted from pounds to kilograms.  

2. **Summary statistics**  
   - For each numeric variable (length, width, depth, weight, quantity per box, boxes on hand, demand), descriptive statistics including mean, standard deviation, minimum, maximum, quantiles, and skewness were computed.  

3. **Correlation matrix**  
   - Pearson correlation coefficients were calculated between all numeric variables [4].  
   - The resulting correlation matrix is saved and used for reference during validation.  

4. **Conditional rules**  
   - Length was discretized into bins to capture distributional variations, following established methods for conditional synthetic generation [1].  
   - For each bin, the 10th, 50th, and 90th percentiles of width, depth, and weight were computed.  
   - Bin counts were retained for probability-weighted sampling.

5. **Ratio statistics**  
   - Ratios between width and length (W/L), depth and width (D/W), and weight and volume (WT/Vol) were computed.  
   - Quantiles (10th, 50th, 90th) of each ratio were extracted to define plausible bounds for synthetic sampling.  
   - Using ratios to enforce plausible relationships is consistent with prior approaches in industrial part synthesis and dimensional consistency modeling [2,5].  

All extracted statistics were saved as CSV and JSON files for use by the synthetic data generation pipeline.

---

## 3. Synthetic Data Generation Methodology

Synthetic parts are generated using the following approach:

1. **Length selection**  
   - A length bin is chosen probabilistically based on bin frequencies from the confidential dataset.  
   - The length is then sampled uniformly within the bin range [1].

2. **Dimension sampling**  
   - Width, depth, and weight are sampled uniformly between the 10th and 90th percentiles of the respective bin [2].

3. **Ratio-based corrections**  
   - Width is clipped to the plausible W/L ratio range.  
   - Depth is clipped to the plausible D/W ratio range.  
   - Weight is clipped to the plausible weight-to-volume ratio range [2,5].

4. **Additional variables**  
   - Quantity per box, boxes on hand, and demand are sampled independently within predefined integer ranges.  
   - Identifiers (item ID and description) are generated to uniquely tag each synthetic part.

5. **Unit conversion for synthetic data**  
   - All length-related variables are returned in millimeters.  
   - Weight is returned in kilograms.  

This approach ensures that synthetic data reflects the overall distribution and inter-variable relationships observed in the confidential dataset, while preventing the reconstruction of individual confidential records. Use of ratio-based clipping is consistent with best practices for industrial and manufacturing datasets [2,5].

---

## 4. Validation and Statistical Consistency

The synthetic generator does not explicitly enforce correlations. However, validation against the summary statistics ensures plausibility:

- **Summary statistics comparison**: mean, standard deviation, min/max, and quantiles of synthetic variables are compared to the confidential dataset.  
- **Distribution comparison**: histograms and boxplots of synthetic variables are compared to confirm plausible ranges [3].  
- **Ratio validation**: W/L, D/W, and weight-to-volume ratios of synthetic parts are checked to ensure they remain within plausible bounds.

The correlation matrix of the synthetic dataset is also compared to the confidential dataset for reference.

---

## 5. Advantages and Limitations

**Advantages:**  
- Preserves aggregate statistical properties of the confidential dataset [1,3].  
- No individual records are exposed, maintaining confidentiality.  
- Generation process is transparent, reproducible, and adjustable based on updated summary statistics.

**Limitations:**  
- Correlations between variables are only implicitly reflected through ratio-based clipping.  
- Extremes and multimodal patterns present in the confidential dataset may not be fully captured.  
- Quantity per box, boxes on hand, and demand are sampled independently.

---

## 6. Conclusion

The synthetic data generation pipeline provides a principled approach for producing realistic part-level datasets while preserving confidentiality. The methodology relies solely on summary statistics and derived constraints from the confidential dataset, following established synthetic tabular data generation practices [1–5].

---

## References

1. Abay, N. C., Zhou, Y., Kantarcioglu, M., Thuraisingham, B., & Sweeney, L. (2018). Privacy Preserving Synthetic Data Release Using Deep Learning. *arXiv preprint arXiv:1803.09381*.  
2. Xu, L., Skoularidou, M., Cuesta-Infante, A., & Veeramachaneni, K. (2019). Modeling Tabular data using Conditional GAN. *Advances in Neural Information Processing Systems (NeurIPS)*, 32.  
3. Jordon, J., Yoon, J., & van der Schaar, M. (2018). PATE-GAN: Generating Synthetic Data with Differential Privacy Guarantees. *arXiv preprint arXiv:1802.06739*.  
4. Benesty, J., Chen, J., Huang, Y., & Cohen, I. (2009). Pearson correlation coefficient. In *Noise Reduction in Speech Processing* (pp. 1–4). Springer.  
5. Winkler, R. L. (2002). Methods for Synthetic Data Generation. *Journal of Official Statistics*, 18(2), 161–178.
