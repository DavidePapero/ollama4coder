# -*- coding: utf-8 -*-

# Copyright 2026 Infantino Davide
#
# Licensed under the EUPL, Version 1.2 as soon they will be approved by the 
# European Commission - subsequent versions of the EUPL (the "Licence");
# 
# You may not use this work except in compliance with the Licence.
# You may obtain a copy of the Licence at:
#
# https://interoperable-europe.ec.europa.eu/collection/eupl/eupl-text-eupl-12
#
# Unless required by applicable law or agreed to in writing, software distributed under the Licence is distributed on an "AS IS" basis,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the Licence for the specific language governing permissions and limitations under the Licence.


import datetime
import time
import typing
import datetime

class HumanDiffTime:
    @staticmethod
    def from_seconds(total_seconds: int) -> str:
        """Trasforma secondi totali in una stringa HH:MM:SS."""

        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    @staticmethod
    def from_date(start_dt: datetime.datetime, end_dt: datetime.datetime) -> str:
        """Calcola la differenza tra due datetime e restituisce una stringa formattata HH:MM:SS."""
        total_seconds = int((end_dt - start_dt).total_seconds())
        return HumanDiffTime.from_seconds(total_seconds)

class QuandoFinisco():
    def __init__(self, _min_ : int, _max_ : int, dtStart : datetime.datetime | None = None) -> None:
        self._min_ = _min_
        self._max_ = _max_
        # tempo per il calcolo del tempo in generale 
        self.dtStart : datetime.datetime = dtStart if dtStart else datetime.datetime.now()
        # tempo per l'esecuzione del ciclo stretto
        self._time_start_ : float = time.time()

    def Calcola(self, index : int) -> typing.Tuple[float, float] :
        if index <= self._min_ or index >= self._max_:
            return (0.0, 0.0)

        len_dati : int = self._max_ - self._min_
        delta : float = time.time() - self._time_start_
        secondi_rimanenti : float = (delta / (index-self._min_)) * (len_dati - (index-self._min_))

        #perc = float(index - self._min_) / float(len_dati)
        perc = float(index) / float(self._max_)

        return (perc, secondi_rimanenti)

    def Stampa(self, index : int) :
        percentage, remaining_seconds = self.Calcola(index)
        dtEndSub = datetime.datetime.now()
        dt = dtEndSub + datetime.timedelta(seconds=remaining_seconds)
        s = dt.isoformat(sep = ' ', timespec = 'seconds')
        perc = percentage * 100
        print(f'{index}/{self._max_} - {perc:.2f}% - Fine: {s} ', end='\r')

    def Fine(self) -> tuple[str,str]:
        dtEnd = datetime.datetime.now()
        adesso : str = dtEnd.isoformat(sep = ' ', timespec = 'seconds')
        tempo = HumanDiffTime(self.dtStart, dtEnd)

        return (adesso, tempo)
