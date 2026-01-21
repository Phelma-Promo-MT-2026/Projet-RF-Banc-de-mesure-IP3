import csv
import bisect


class TxCalibration:
    def __init__(self, csv_path):
        # Load calibration grid from CSV: frequencies (rows) × commanded powers (columns)
        self.freqs = []      # List of RF frequencies (Hz) corresponding to each row
        self.powers = []     # List of commanded TX powers (dBm) corresponding to each column
        self.grid = []       # 2D matrix of measured values or corrections (dBm)

        # Read entire CSV file into memory
        with open(csv_path, newline="") as f:
            reader = csv.reader(f)
            rows = list(reader)

        # First line: power headers (skip first column which is frequency)
        self.powers = [float(x) for x in rows[0][1:]]
        # Next lines: frequency in first column, then grid values
        for r in rows[1:]:
            f_rf = float(r[0])
            self.freqs.append(f_rf)
            self.grid.append([float(x) for x in r[1:]])

    def _nearest_index(self, values, x):
        # Return index of the closest value to x in a sorted list
        idx = bisect.bisect_left(values, x)
        if idx == 0:
            return 0
        if idx == len(values):
            return len(values) - 1
        before = values[idx - 1]
        after = values[idx]
        return idx - 1 if abs(x - before) <= abs(x - after) else idx

    def get_correction(self, f_rf_user, p_tx_user):
        # Look up gain correction for given RF frequency and TX power
        # Check that requested frequency is inside calibration table bounds
        if not (self.freqs[0] <= f_rf_user <= self.freqs[-1]):
            raise ValueError("f_rf en dehors de l’abaque")
        # Check that requested power is inside calibration table bounds
        if not (self.powers[0] <= p_tx_user <= self.powers[-1]):
            raise ValueError("P_tx en dehors de l’abaque")

        # Find nearest grid indices for frequency and power
        i_f = self._nearest_index(self.freqs, f_rf_user)
        i_p = self._nearest_index(self.powers, p_tx_user)

        # Measured TX level at closest calibration point
        # Convention-dependent: could be measured power or an offset
        meas_tx = self.grid[i_f][i_p]
        # Correction to apply so that commanded power matches target
        corr_db = p_tx_user - meas_tx
        print("p_tx_user:", p_tx_user)
        print("corr_db:", corr_db)

        # Reference points actually used from the grid
        f_ref = self.freqs[i_f]
        p_ref = self.powers[i_p]
        return corr_db, f_ref, p_ref
