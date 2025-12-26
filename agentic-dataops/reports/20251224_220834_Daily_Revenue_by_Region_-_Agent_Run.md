# Daily Revenue by Region - Agent Run

## Loaded Sales

Rows: 5  |  Path: data\sales.csv

## Loaded Regions

Rows: 3  |  Path: data\regions.csv

## Input Profile

{
  "rows": 5,
  "cols": 5,
  "columns": {
    "order_id": {
      "dtype": "int64",
      "nulls": 0,
      "null_pct": 0.0,
      "nunique": 5,
      "min": 1.0,
      "max": 5.0,
      "mean": 3.0,
      "std": 1.5811388300841898
    },
    "date": {
      "dtype": "object",
      "nulls": 0,
      "null_pct": 0.0,
      "nunique": 2,
      "top_values": {
        "2025-01-02": 3,
        "2025-01-01": 2
      }
    },
    "region": {
      "dtype": "object",
      "nulls": 0,
      "null_pct": 0.0,
      "nunique": 3,
      "top_values": {
        "APAC": 3,
        "EMEA": 1,
        "AMER": 1
      }
    },
    "revenue": {
      "dtype": "int64",
      "nulls": 0,
      "null_pct": 0.0,
      "nunique": 5,
      "min": 700.0,
      "max": 1200.0,
      "mean": 920.0,
      "std": 192.35384061671346
    },
    "product_id": {
      "dtype": "object",
      "nulls": 0,
      "null_pct": 0.0,
      "nunique": 3,
      "top_values": {
        "P1": 2,
        "P2": 2,
        "P3": 1
      }
    }
  }
}

## Transform

Applied recipe successfully.

## Data Quality

Issues:
- Column missing for unique: order_id

## Save

Saved to clean\revenue_by_region.parquet

## Output Profile

{
  "rows": 4,
  "cols": 4,
  "columns": {
    "date_day": {
      "dtype": "object",
      "nulls": 0,
      "null_pct": 0.0,
      "nunique": 2,
      "top_values": {
        "2025-01-01": 2,
        "2025-01-02": 2
      }
    },
    "region": {
      "dtype": "object",
      "nulls": 0,
      "null_pct": 0.0,
      "nunique": 3,
      "top_values": {
        "APAC": 2,
        "EMEA": 1,
        "AMER": 1
      }
    },
    "region_name": {
      "dtype": "object",
      "nulls": 0,
      "null_pct": 0.0,
      "nunique": 3,
      "top_values": {
        "Asia Pacific": 2,
        "Europe, Middle East & Africa": 1,
        "Americas": 1
      }
    },
    "revenue": {
      "dtype": "int64",
      "nulls": 0,
      "null_pct": 0.0,
      "nunique": 4,
      "min": 700.0,
      "max": 2100.0,
      "mean": 1150.0,
      "std": 645.4972243679028
    }
  }
}

## Reflection

Pass: False
Issues: 
- DQ checks failed.
