# Cooperative Multi-Agent Tabular Q-Learning for Sequential Anomaly Detection in LoRaWAN Traffic

**Research code and reproducibility resources** for a cooperative, tabular reinforcement-learning framework for sequential anomaly detection in heterogeneous LoRaWAN traffic.

> **Research status:** The E3-R83 experiments are **development-only and non-confirmatory**. Results are based on constructed synthetic episodes; they must not be presented as independently validated performance on raw real-world attacks.

## Overview

The framework investigates sequential anomaly-detection policies using four functionally specialized tabular Q-learning agents:

- **Radio:** radio-link observations such as RSSI and SNR.
- **Temporal:** message inter-arrival behaviour.
- **PHY:** selected physical-layer-related traffic attributes.
- **Protocol:** frame-counter progression and related protocol behaviour.

A tabular coordinator combines specialist evidence and chooses among **WAIT**, **INSPECT**, and **ALERT**. Inspection allows the policy to acquire additional specialist evidence at an explicit cost. The research evaluates the trade-offs between detection sensitivity, false alarms, sequential decisions, and coordinator-state complexity.

The experimental comparison includes **Centralized**, **Four-Q**, **No PHY**, **No Protocol**, **No Radio**, and **No Temporal** configurations.

## Repository contents

| Path | Purpose |
| --- | --- |
| `core/` | Core framework implementation |
| `data/` | Dataset inputs and/or prepared episode resources |
| `inputs/` | Additional experimental inputs |
| `models/`, `models_r72/` | Model and checkpoint resources |
| `results/` | Experimental output files |
| `r83_campaign.py` | E3-R83 campaign implementation |
| `r82_protocol_manifest.json` | Protocol/freeze-readiness metadata |
| `README_R83_PT.md` | Detailed R83 execution notes in Portuguese |
| `README_PT.md` | General Portuguese documentation |
| `requirements.txt` | Python dependencies |
| `33_R83_SMOKE.bat` | Short R83 smoke test |
| `34_R83_PILOT_5_SEEDS.bat` | R83 five-seed pilot |
| `35_R83_FULL_20_SEEDS.bat` | R83 twenty-seed development campaign |

Earlier R70–R82 scripts and accompanying documentation are retained to document the development and auditing history.

## Requirements

- Python environment compatible with the dependencies below.
- Windows for the supplied `.bat` launchers.

Dependencies specified in `requirements.txt`:

```text
numpy>=1.24,<3
pandas>=2.0,<3
scikit-learn>=1.3,<2
```

Install them from the repository root:

```powershell
python -m pip install -r requirements.txt
```

Alternatively, the repository includes `00_INSTALL_ALL.bat` and `01_CHECK_ENVIRONMENT.bat` for its Windows workflow.

## Running the E3-R83 experiments

From the repository root on Windows, first check the environment and dataset preparation instructions in `README_PT.md` and `README_R83_PT.md`.

```bat
01_CHECK_ENVIRONMENT.bat
02_PREPARE_DATASETS.bat
33_R83_SMOKE.bat
34_R83_PILOT_5_SEEDS.bat
35_R83_FULL_20_SEEDS.bat
```

Run the stages **sequentially**, verifying each stage before proceeding. The full twenty-seed campaign can be time-consuming. Do not rerun data preparation over curated files without first reviewing the scripts and preserving any existing outputs.

The R83 documentation identifies the following outputs under `results/`:

- `r83_campaign_manifest.json`
- `r83_metrics.csv`
- `r83_episode_predictions.csv`
- `r83_summary.csv`
- `R83_RELATORIO_PT.md`

See `README_R83_PT.md` for campaign-specific settings and restrictions.

## Data provenance and evaluation scope

The broader research references the **LoRaWAN Traffic Analysis Dataset** (Zenodo record [8090619](https://zenodo.org/records/8090619)) as an upstream source. The E3-R83 repository documentation specifies that its `data/train.csv.gz` contains **original synthetic episodes** and that `test.csv.gz` is **not read** by the R83 campaign.

Accordingly, the E3-R83 results describe performance on synthetic development episodes, **not direct evaluation on the original real-world traffic captures**. Any claim of derivation from the upstream Zenodo data should be supported by the relevant data-generation scripts and provenance records.

The R83 campaign uses training-only calibration and does not constitute an independent held-out test. The validation scenarios had been explored during development. The evaluation therefore remains **exploratory/non-confirmatory**.

## Experimental interpretation

The twenty-seed development campaign investigates six architectures and reports classification, sequential-decision, ablation, and computational metrics. In the analysed campaign, the cooperative Four-Q coordinator used fewer stored Q-table entries and exhibited a lower false-positive rate than the centralized comparator, but it also had lower recall and F1-score. MCC remained low, and inference latency was comparable.

These observations characterize **architectural trade-offs**; they do **not** establish superior overall detection performance or operational deployment readiness. The number of coordinator Q-table entries is not a substitute for measuring total memory, end-to-end runtime, or energy consumption.

## Reproducibility considerations

- Preserve the reported random seeds, experiment manifests, and original output files.
- Distinguish pilot runs from the twenty-seed development campaign.
- Do not tune hyperparameters on the same validation episodes and then label the outcome independent confirmation.
- Coordinator training time excludes shared specialist-training overhead unless explicitly stated otherwise.
- Equal transition counts do not imply equal model capacity or equal total computational cost.
- Confirmatory assessment requires a frozen protocol and previously unseen evaluation data.

## Citation

If you use this repository, cite the associated article **once its final bibliographic details are available**. Until then, refer to this repository by its URL:

https://github.com/prof-luispires/C-MA-TQ-learning-framework

## License

No license is declared in this README. Please consult the repository for a `LICENSE` file before assuming permission to reuse or redistribute the code. Repository visibility alone does not grant an open-source license.

## Contact and maintenance

Repository owner: [prof-luispires](https://github.com/prof-luispires).

For technical questions, use the repository's GitHub Issues section, if enabled.
