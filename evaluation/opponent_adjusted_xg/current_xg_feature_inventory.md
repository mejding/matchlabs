# Current Production xG Feature Inventory

These raw xG-family features are active in the current production feature set.

| feature | family | active_in_production | calculation |
| --- | --- | --- | --- |
| home_xg_avg | xG average | True | Rolling last-5 team xG/xGA derived before each fixture in train_model.build_features. |
| away_xg_avg | xG average | True | Rolling last-5 team xG/xGA derived before each fixture in train_model.build_features. |
| home_xga_avg | xGA average | True | Rolling last-5 team xG/xGA derived before each fixture in train_model.build_features. |
| away_xga_avg | xGA average | True | Rolling last-5 team xG/xGA derived before each fixture in train_model.build_features. |
| home_xg_diff | xG differential | True | Rolling last-5 team xG/xGA derived before each fixture in train_model.build_features. |
| away_xg_diff | xG differential | True | Rolling last-5 team xG/xGA derived before each fixture in train_model.build_features. |