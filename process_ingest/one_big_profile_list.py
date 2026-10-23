from pathlib import Path
import re
import pandas as pd

'''
Creates a .csv of all valid profiles (no overload, or erroneous force values)
Grouped by pit_id, smp_profile_paths, scope_profile_paths, ram_profile_path
'''

def clean_pit_id(val: str) -> str:
    """Extracts base SITE_YYYYMMDD by stripping scope/smp suffixes and extensions."""
    s = str(val).strip()
    s = re.sub(
        r"([._]smp|[._]scope)?(\.csv)?$", "", s, flags=re.IGNORECASE
    )
    return s


def build_profile_summary(
    smp_file: str, scope_file: str, output_file: str = "all_profiles.csv"
):
    # 1. Read input Excel files
    df_smp = pd.read_excel(smp_file)
    df_scope = pd.read_excel(scope_file)

    # 1.5 Filter out flagged profiles (toss == 1 or overload == 1)
    smp_valid = df_smp[
        (df_smp["toss"] == 0) & (df_smp["overload"] == 0)
    ].copy()
    scope_valid = df_scope[
        (df_scope["toss"] == 0) & (df_scope["overload"] == 0)
    ].copy()

    # 2. Extract column 0 (pit_id raw) and profile filename column 1
    smp_col_0, smp_col_1 = smp_valid.columns[0], smp_valid.columns[1]
    scope_col_0, scope_col_1 = scope_valid.columns[0], scope_valid.columns[1]

    # Clean pit_id using valid dataframes
    smp_valid["pit_id"] = smp_valid[smp_col_0].apply(clean_pit_id)
    scope_valid["pit_id"] = scope_valid[scope_col_0].apply(clean_pit_id)

    # Directory base paths
    smp_base_dir = Path("data/pen_profiles/smp_profiles_exports")
    scope_base_dir = Path("data/pen_profiles/Snow_Scope")
    ram_base_dir = Path("data/pen_profiles/ram_files")

    # Combine directory paths with filenames
    smp_valid["profile_path"] = smp_valid[smp_col_1].apply(
        lambda f: str(smp_base_dir / str(f))
    )
    scope_valid["profile_path"] = scope_valid[scope_col_1].apply(
        lambda f: str(scope_base_dir / str(f))
    )

    # 3. Group valid profiles separately by pit_id
    smp_grouped = (
        smp_valid.groupby("pit_id")["profile_path"]
        .apply(lambda paths: ", ".join(paths.astype(str).unique()))
        .rename("smp_profile_paths")
    )

    scope_grouped = (
        scope_valid.groupby("pit_id")["profile_path"]
        .apply(lambda paths: ", ".join(paths.astype(str).unique()))
        .rename("scope_profile_paths")
    )

    # 4. Collect all unique pit_ids across both datasets
    df_smp["pit_id"] = df_smp[df_smp.columns[0]].apply(clean_pit_id)
    df_scope["pit_id"] = df_scope[df_scope.columns[0]].apply(clean_pit_id)
    all_pit_ids = sorted(
        list(set(df_smp["pit_id"]).union(set(df_scope["pit_id"])))
    )

    # 5. Merge into separate columns
    summary_df = pd.DataFrame({"pit_id": all_pit_ids})
    summary_df = summary_df.merge(smp_grouped, on="pit_id", how="left")
    summary_df = summary_df.merge(scope_grouped, on="pit_id", how="left")

    # Replace NaNs with empty strings for missing profiles
    summary_df["smp_profile_paths"] = summary_df["smp_profile_paths"].fillna("")
    summary_df["scope_profile_paths"] = summary_df[
        "scope_profile_paths"
    ].fillna("")

    # Construct RAM profile path
    summary_df["ram_profile_path"] = summary_df["pit_id"].apply(
        lambda pid: str(ram_base_dir / f"{pid}_sram.csv")
    )

    # 6. Save to output CSV
    summary_df.to_csv(output_file, index=False)
    print(
        f"Summary created with {len(summary_df)} unique pit_ids: {output_file}"
    )


if __name__ == "__main__":
    build_profile_summary(
        smp_file="../data/smp_cleaning_all.xlsx",
        scope_file="../data/scope_cleaning_all.xlsx",
        output_file="all_profiles.csv",
    )