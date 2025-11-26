"""
Package Import
"""
import yfinance as yf
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import quantstats as qs
import gurobipy as gp
import warnings
import argparse
import sys

"""
Project Setup
"""
warnings.simplefilter(action="ignore", category=FutureWarning)

assets = [
    "SPY",
    "XLB",
    "XLC",
    "XLE",
    "XLF",
    "XLI",
    "XLK",
    "XLP",
    "XLRE",
    "XLU",
    "XLV",
    "XLY",
]

# Initialize Bdf and df
Bdf = pd.DataFrame()
for asset in assets:
    raw = yf.download(asset, start="2012-01-01", end="2024-04-01", auto_adjust = False)
    Bdf[asset] = raw['Adj Close']

df = Bdf.loc["2019-01-01":"2024-04-01"]

"""
Strategy Creation

Create your own strategy, you can add parameter but please remain "price" and "exclude" unchanged
"""


class MyPortfolio:
    """
    NOTE: You can modify the initialization function
    """

    def __init__(self, price, exclude, lookback=50, gamma=0):
        self.price = price
        self.returns = price.pct_change().fillna(0)
        self.exclude = exclude
        self.lookback = lookback
        self.gamma = gamma

    def calculate_weights(self):
        # Get the assets by excluding the specified column
        assets = self.price.columns[self.price.columns != self.exclude]

        # Calculate the portfolio weights
        self.portfolio_weights = pd.DataFrame(
            index=self.price.index, columns=self.price.columns
        )

        """
        TODO: Complete Task 4 Below
        """
        eps = 1e-8
        assets = self.price.columns[self.price.columns != self.exclude]

        lookback_ret = 120     # 動能視窗
        lookback_vol = 30      # 波動視窗
        lookback_ma = 200      # 均線視窗

        # 預先算好 200MA（避免每次 loop 重算）
        ma200 = self.price[assets].rolling(lookback_ma).mean()

        for i in range(len(self.price)):
            date = self.price.index[i]

            # ---- Step 0: 資料不足時（前 200 天）全部設為 0 ----
            if i < max(lookback_ret, lookback_ma):
                self.portfolio_weights.loc[date, assets] = 0
                continue

            # ---- Step 1: 偵測哪些資產突破 200MA ----
            valid_assets = [
                a for a in assets 
                if self.price[a].iloc[i] > ma200[a].iloc[i]
            ]

            if len(valid_assets) == 0:
                # 沒有資產站上均線 → 全部 0
                self.portfolio_weights.loc[date, assets] = 0
                continue

            # ---- Step 2: 動能排名（只在 valid assets 裡比較） ----
            past_returns = self.price[valid_assets].iloc[i - lookback_ret:i].pct_change().sum()

            # 只選 top1
            top1 = past_returns.sort_values(ascending=False).head(3).index

            # ---- Step 3: 計算 top1 的波動（risk parity，top1 → 權重 = 1） ----
            vol = self.returns[top1].iloc[i - lookback_vol:i].std() + eps
            inv_vol = 1 / vol
            w = inv_vol / inv_vol.sum()   # top1 → w = [1]

            # ---- Step 4: 初始化今日所有資產 = 0 ----
            self.portfolio_weights.loc[date, assets] = 0

            # ---- Step 5: top1 權重填上 ----
            self.portfolio_weights.loc[date, top1] = w.values

        # SPY 欄位 = 0
        self.portfolio_weights[self.exclude] = 0.0

        
        """
        TODO: Complete Task 4 Above
        """

        self.portfolio_weights.ffill(inplace=True)
        self.portfolio_weights.fillna(0, inplace=True)

    def calculate_portfolio_returns(self):
        # Ensure weights are calculated
        if not hasattr(self, "portfolio_weights"):
            self.calculate_weights()

        # Calculate the portfolio returns
        self.portfolio_returns = self.returns.copy()
        assets = self.price.columns[self.price.columns != self.exclude]
        self.portfolio_returns["Portfolio"] = (
            self.portfolio_returns[assets]
            .mul(self.portfolio_weights[assets])
            .sum(axis=1)
        )

    def get_results(self):
        # Ensure portfolio returns are calculated
        if not hasattr(self, "portfolio_returns"):
            self.calculate_portfolio_returns()

        return self.portfolio_weights, self.portfolio_returns


if __name__ == "__main__":
    # Import grading system (protected file in GitHub Classroom)
    from grader_2 import AssignmentJudge
    
    parser = argparse.ArgumentParser(
        description="Introduction to Fintech Assignment 3 Part 12"
    )

    parser.add_argument(
        "--score",
        action="append",
        help="Score for assignment",
    )

    parser.add_argument(
        "--allocation",
        action="append",
        help="Allocation for asset",
    )

    parser.add_argument(
        "--performance",
        action="append",
        help="Performance for portfolio",
    )

    parser.add_argument(
        "--report", action="append", help="Report for evaluation metric"
    )

    parser.add_argument(
        "--cumulative", action="append", help="Cumulative product result"
    )

    args = parser.parse_args()

    judge = AssignmentJudge()
    
    # All grading logic is protected in grader_2.py
    judge.run_grading(args)
