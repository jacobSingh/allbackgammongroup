import numpy as np
class ELO:

    def __init__(self, rampup = 0):
        self.rampup = rampup

    def get_win_chance(self, elo1, elo2, length):
        exp = -1*(elo1-elo2) * np.sqrt(length)/2000
        return 1/(1+10**exp)

    def compute_change(self, elo_winner, elo_loser, length, winner_xp, loser_xp):
        elo_winner = int(elo_winner)
        elo_loser = int(elo_loser)
        points = 4 * np.sqrt(length)

        winner_change = (1 - self.get_win_chance(elo_winner, elo_loser, length)) * points
        loser_change = points * self.get_win_chance(elo_loser, elo_winner, length)

        if (type(loser_xp) is "NaN"):
            raise Exception("Loser XP is NaN")

        winner_change = winner_change * self.get_rampup_magnitude(int(winner_xp))
        loser_change = loser_change * self.get_rampup_magnitude(int(loser_xp))
        return (winner_change, loser_change * -1)

    def get_rampup_magnitude(self, xp):
        if (self.rampup > xp):
            return (((self.rampup + 100) - xp) / 100)
        return 1
