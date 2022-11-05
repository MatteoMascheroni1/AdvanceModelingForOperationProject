# PROGETTO DI ADVANCED MODELING FOR OPERATION

## Aggiornamenti
* Con l'ultimo commit ho sistemato tutta la conversione in secondi, controllate se per caso mi sono lasciato indietro qualcosa che
può benissimo essere :(.
* Ho fatto il refactoring della funzione read line info e nel file line_info.csv ho aggiunto anche il peso della singola UL
* Ho setuppato il data collector e il batch runner **Occhio che il datacollector funziona solo se c'è uno scheduler che si chiama
scheduler, ieri sera ho smattato**


## To do
* Suddivisione ulteriore in main e classes (ci ho provato ma è un po' compli, forse è meglio se lo facciamo tutti insieme)
* Aggiornamento del modello con logiche fisiche (velocità, potenza ecc...) un pochettino più avanzate



## Tugger train conspumption and speed

* Il consumo viene calcolato secondo lo standard internazionale e viene recepito dai diversi paesi (DIN EN 16796 quello della still che è tedesca, mentre la CAT mantiene l'originale EN16796) quindi anche se dovessimo lasciarlo come consumo medio non penso sarebbe un grosso problema. Ho trovato comunque il testo della BS EN16796 che invece è lo standard internazionale recepite dalla British Standards Online. Visto che gli standard costano tipo 100€ l'uno direi di fare riferimento al BS EN16796 che almeno lo abbiamo incluso con il poli.
* Nel file **ntr30n2ntr50n2 sales brochure spec sheet english final.pdf** e nel file **LTX_20_T04_50_iGo_EN_TD.pdf** ci sono i grafici della velocità in base ai newton trainati, nel primo un po' più professionali, nel secondo un po' più spannometrici. Non ho trovato dati più attendibili per quelli a guida autonoma ma non penso che possano essere molto diversi.



## Aggiornamento 04/11

* I tempi in secondi sono giusti
* Abbiamo unificato tutte le versioni del codice
* Abbiamo aggiunto il controllo sul peso
* Aggiornato la distanza e la velocità nel modulo utils, al momento la velocità è una costante ma si potrà passare una variabile qualunque (quindi anche renderla dipendente dal peso)
* Abbiamo rimosso momentaneamente il data collector e il batch runner perchè secondo noi era inutile.


## Aggiornamento 05/11
* Fixato la condizione sul peso, ora controlla prima di aggiornare self.weight e se passa la condizione allora lo aggiorna definitivamente. Controllato anche l'inizializzazione di self.weight = 0 quando fa l'unloading.
