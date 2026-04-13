# Customer Segmentation with RFM & Unsupervised Learning

## Business Problem

E-commerce companies often struggle to understand the diversity of their customer base.
Without clear segmentation, marketing teams waste budget on broad campaigns, fail to retain valuable customers, and miss opportunities for personalization.

How can we identify distinct customer groups to improve retention, loyalty, and revenue?

## Proposed Solution

RFM analysis (Recency, Frequency, Monetary) combined with K-Means clustering to uncover meaningful customer segments in the Online Retail (UCI) dataset.

**Key steps:**

- Data cleaning and exploratory data analysis (EDA)
- RFM feature engineering
- Log transformation and standardization
- K-Means clustering with elbow & silhouette analysis
- PCA for 2D and 3D visualization
- Cluster profiling and business interpretation
- Radar charts to compare customer groups

## Results — 5 Customer Segments

| Cluster | Persona | Profile |
|---------|---------|---------|
| 4 | VIP / Premium | Very recent · very frequent · highest spenders |
| 1 | Loyal High-Value | Regular buyers · strong revenue |
| 2 | Potential Loyalists | Good spenders · recently inactive |
| 0 | Occasional Buyers | Low frequency · low spend |
| 3 | At-Risk Customers | Long inactivity · low lifetime value |

## Technologies

Python · Pandas · NumPy · Scikit-learn · K-Means · PCA · Matplotlib · Seaborn

## Business Impact

- **Targeted marketing** — personalized campaigns per segment
- **Higher retention** — identify at-risk customers before they churn
- **Revenue focus** — prioritize VIPs and high-value clusters
- **Budget efficiency** — allocate marketing spend where it matters most

## Visualizations

### PCA Clustering (2D)

<img width="844" height="624" alt="pca_clusters" src="visuals/pca_clusters.png" />

### Radar Charts — Cluster Profiles

<img width="1196" height="1589" alt="radar_clusters" src="visuals/radar_clusters.png" />

### RFM Distributions

<img width="790" height="1490" alt="rfm_distribution" src="visuals/rfm_distribution.png" />

### Top 10 Products by Revenue (EDA)

<img width="1110" height="701" alt="top_10_products" src="visuals/top_10_products.png" />

## Possible Next Steps

- Real-time customer monitoring dashboard
- RFM + product preferences for deeper segmentation
- Alternative clustering methods: GMM, DBSCAN, hierarchical
- Marketing recommendation engine based on cluster profiles
