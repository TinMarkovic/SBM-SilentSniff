---
## Uvod

Set alata za Wireless Security testiranje, istražen i ukomponiran kao projekt iz kolegija Sigurnost Bežičnih Mreža na FESB-u. Ovaj projekt kao cilj ima demonstriranje prisluškivanja klijenata na bežičnoj mreži. Kroz predavanja i laboratorijske vježbe tijekom cijelog semestra, projekt je kroz nekoliko faza stalnog razvijanja došao do trenutnog stanja. Kao takav je primjenjiv, iako je preporučena upotreba samo u službi testiranja sigurnosti i demonstriranja osnovnih principa bežičnih mreža.

Projekt je namjenjen prisluškivanju mreže i korisnika na istoj - sa nekoliko obaveznih elemenata:

* Prisluškivanje bez ostavljanja tragova
* Praćenje korisnikovih navika
* Praćenje tijeka kretanja i kroz sigurne kanale

Ovaj niz zahtjeva zahtjeva i odreðen set alata. Primjenjena su dva glavna alata za sam projekt:

* Scapy
* Dot11Decrypt

Razvoj se temelji na uspostavljanju Dot11Decrypt tunela za dekriptiranje WPA2 paketa, te pisanju Python i Scapy koda za analizu paketa i kretanja korisnika. 

Uz ovo, sporedni alati su bili i set alata iz Aircrack-ng paketa, korišteni za olakšavanje skeniranja prometa, iako nisu ključni funkcioniranju samog projekta.

---
## Metodologija

Cijeli program se oslanja na jednostavnom toku rada:

Airmon-ng gasi i diže hardware računala, mrežnu karticu, stavljajući je u monitoring mode. O monitoring modu će biti više kasnije.

Airodump-ng fokusira monitoring alat da prati odreðeni kanal. Na ovaj način se lakše filtrira promet i lakše prati bežični promet meta.

Dot11decrypt pretvara enkriptirani kanal u dekriptirani stream, nakon hvatanja handshake-a klijenata. 

Silentsniff.py sluša dekriptirane pakete i veže ih uz MAC adrese, te prati ostatak metrika.

Svaki od koraka će se detaljno proučiti i podesiti.

---
## Aircrack-ng komponente

Airmon-ng se koristi za provjeru mrežnih sučelja računala. Budući da je mrežna kartica pod kontrolom drivera računala, često je preporučivo upaliti `airmon-ng check kill` komandu, koja ubija procese zakačene na mrežno sučelje. Na ovaj način, hardware je slobodan za preuzimanje.

Pokreće se monitoring mod na tom sučelju komandom `airmon-ng start <if>` gdje je <if> naziv interface-a. Provjeru svih sučelja možemo izvršiti zovući airmon-ng bez ikakvih argumenata.

---
### Monitoring Mode

Mrežne kartice za bežičnu vezu imaju nekoliko modova: Master, Managed, Ad hoc, Mesh, Repeater, Promiscuous i Monitor.

Monitor (ili RFMON) je mod u kojem hardware računala (mrežna kartica) prati sav promet u zraku. Za razliku od promiscuous moda, monitor mod se ne asocira niti sa jednom mrežom, pa je potpuno nevidljiv promatračima na mreži. 

Općenito, wireless adapter u monitor modu nije u mogućnosti emitirati signal - te je potrebno imati sučelje isključivo za monitoring mod. Dosta često monitor mod implementacija ne provjerava CRC bitove, pa je i šansa za koruptiranim podacima znatno veća. Podrška operacijskih sustava za ovaj mod je često upitna, te je to jedan od glavnih razloga zašto se koristi Airmon-ng.

---

Kada je sučelje u monitoring modu, za bolju kvalitetu slušanja dobro ga je fokusirati na jedan kanal bežične mreže. Za to služi airodump-ng alat, s kojim putem promatranja provjerimo kanal mreže koju ciljamo, te onda fiksiramo snimanje na taj kanal. To je jednostavno uraditi putem komande `airodum-ng mon0` (ili neki drugi interface), te onda sa odabranim kanalom zamijeniti <num> u `airodump-ng --channel <num> mon0`.

---
## Dot11Decrypt



[Dot11Decrypt](https://github.com/mfontanini/dot11decrypt) je alat za transformiranje stream-a paketa iz enkriptiranog signala u de-kriptirane podatke. Dot11Decrypt *ne* probija enkripciju. 

Aplikacija čita mrežno sučelje tražeći enkriptirani promet. Prethodno analizira EAPOL handshake da prati razmjenu ključeva potrebnu za dekriptiranje WPA2. Jednom kada je paket uspješno dekriptiran, 802.11 okvir (enkriptirani okvir) zamijeni se Ethernet header-om, te je cijeli paket zapisan na novo sučelje, koje bude nazvano `tap` sučelje. Za funkcioniranje zahtjeva SSID i ključ.

---
### WPA2

WPA2 (Wi-Fi Protected Access 2) je sigurnosna tehnologija koja danas prevladava na bežičnim mrežama. WPA2 je zamijenio originalni WPA na svom Wi-Fi hardware-u od 2006, te se bazira na IEEE 802.11i tehnološkom standardu. WPA2 utječe na brzinu mrežne konekcije (budući da ipak jest enkripcija), ali je utjecaj na brzinu obično zanemariv.

WPA2 zaštita se bazira na procesu 4-way handshake-a. On je ukratko sadržan u koracima:
1. AP (Access Point) šalje ANonse (AP Nonce) klijentu, koji je u biti nasumično izabrani integer.
2. Klijent koristi ANonce i PMK (Pairwise Master Key - generiran iz PSK-a, ključa) da generira PTK (Pairwise Transient Key), i pošalje CNonce (Client Nonce) i MAC.
3. AP šalje MAC i GTK (Group Temporal Key) klijentu.
4. Klijent šalje ACK sa MAC-om.

Na ovaj način, klijent i AP razmjene ključeve te onda enkriptiraju promet istima. Ovaj proces treba snimiti da bi taj enkriptirani promet mogli dekriptirati

---

Dot11Decrypt se mora sagraditi iz source koda programa, prije uporabe:

Za građenje (kompajliranje / compile) aplikacije je potreban [libtins library](http://libtins.github.io/). libtins je C++ library za snimanje i građenje paketa na mreži. U biti, libtins je u C++-u što je Scapy u Pythonu. Dot11Decrypt je utemeljen na tom library-u. 

Prvo je potrebno imati relativno novi C++ compiler (g++ 4.6 je provjeren). Nakon toga je potrebno preuzeti library-e sa githuba, te ih na standardan C++ način izgraditi:

```
# Instalirati ovisnosti libtins-a
sudo apt-get install libpcap-dev
sudo apt-get install openssl

# Pripremiti build direktorij (najbolje u folderu samog projekta)
mkdir build
cd build

# Uperiti u root libtins direktorija, te onda izgraditi
cmake ../
make

# Nadograditi sustavne datoteke da prepoznaju libtins
make install

# Te onda ponoviti dio koraka i za Dot11Decrypt
cd ../../dot11decrypt
mkdir build
cd build
cmake ../
make
```

Nakon ovih koraka je dot11decrypt instaliran, i nalazi se u `./dot11decrypt/build/dot11decrypt`. 
 
Pokreće se sa komandom `./dot11decrypt mon0 wpa:AccessPoint:password` gdje se dosljedni elementi zamjene našim postavkama.  

---
## SilentSniff.py

SilentSniff.py je Python file koji uključuje Scapy library da bi demonstrirao njene mogućnosti za čitanje paketa na mreži. Kod je dostupan na ovom repozitoriju, te je poprilično samo-objašnjiv. 

Ukratko, datoteka prati tok paketa koji teku kroz zadani interface. Za svaki paket, pokrene procesiranje istog. Krećući se kroz slojeve, iz paketa pročita MAC adresu i osnovni sadržaj. U trenutnom konceptualnom primjeru, prati korisnikove posjete i HTTP pozive na internetu - ukoliko korisnik skrene sa neosiguranog prometa, prebaci se na praćenje njegova kretanja po sigurnom prometu putem praćenja DNS poziva korisnika, time znamo kretanje kroz domene.

Skripta je relativno lako proširiva sa dodatnim elementima - poput trajnog spremanja paketa, dubljih analiza, te još elemenata koji su potrebni za analizu primljenog podatka. Ovaj primjer je samo konceptualna prezentacija mogućnosti Scapy-a u kombinaciji sa drugim alatima.

---
## Zaključak i rezultati

Napadi poput ovoga nisu detektabilni, jer ne koriste direktan način pristupa mreži - ipak, protiv njih se može braniti praćenjem jednostavnih praksi prilikom korištenja interneta:
* Upotrebom HTTPS stranica gdje se mogu koristiti
* Izbjegavanjem upotrebe ne-HTTPS stranica za osjetljive podatke
* Različite lozinke primjenjivati na HTTP stranicama

Uz to, koristeći sigurni DNS možete se zaštiti od praćenja putem DNS-a. 

Cijeli proces pokretanja aplikacije, jednom kada je instalirana, slijedi:

```
Airmon-ng check kill
Airmon-ng start <if>

Airodump-ng mon0
Airodump-ng --channel <num> mon0

./dot11decrypt mon0 wpa:SSID:PASSWORD

Python silentsniff.py # Interface: tap0
```