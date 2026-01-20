import csv
import bisect

class TxCalibration:
    def __init__(self, csv_path):
        # lectures des axes
        self.freqs = []      # liste des fréquences (Hz) - lignes
        self.powers = []     # liste des puissances commandées (dBm) - colonnes
        self.grid = []       # matrice des corrections (dBm), même taille

        with open(csv_path, newline="") as f:
            reader = csv.reader(f)
            rows = list(reader)

        # première ligne : en-têtes de puissances
        self.powers = [float(x) for x in rows[0][1:]]
        # lignes suivantes : f, puis valeurs
        for r in rows[1:]:
            f_rf = float(r[0])
            self.freqs.append(f_rf)
            self.grid.append([float(x) for x in r[1:]])

    def _nearest_index(self, values, x):
        # renvoie l’index du point le plus proche
        idx = bisect.bisect_left(values, x)
        if idx == 0:
            return 0
        if idx == len(values):
            return len(values) - 1
        before = values[idx - 1]
        after = values[idx]
        return idx - 1 if abs(x - before) <= abs(x - after) else idx

    def get_correction(self, f_rf_user, p_tx_user):
        # contrôles de limites
        if not (self.freqs[0] <= f_rf_user <= self.freqs[-1]):
            raise ValueError("f_rf en dehors de l’abaque")
        if not (self.powers[0] <= p_tx_user <= self.powers[-1]):
            raise ValueError("P_tx en dehors de l’abaque")

        i_f = self._nearest_index(self.freqs, f_rf_user)
        i_p = self._nearest_index(self.powers, p_tx_user)

        meas_tx = self.grid[i_f][i_p]  # par ex. (P_mesurée - P_commandée) ou l’inverse selon ta convention
        corr_db = p_tx_user - meas_tx  # correction à appliquer
        print("p_tx_user:", p_tx_user)
        print("corr_db:", corr_db)
        
        f_ref = self.freqs[i_f]
        p_ref = self.powers[i_p]
        return corr_db, f_ref, p_ref
