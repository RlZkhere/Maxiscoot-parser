import selenium
from selenium import webdriver 
from selenium.webdriver.common.by import By
import pandas as pd
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import requests
import time
import re
import os
import traceback
filedatitecnici='DATI/dati-tecnici.csv'
fileanagrafica='DATI/fileinfo.csv'
filefoto='DATI/foto.csv'
filecompatibilita='DATI/compatibilita.csv'
#CREAZIONE FILE CSV
if not os.path.isfile(fileanagrafica):
 f=open(fileanagrafica,'a')
 f.write('SKU;TITOLO;MARCHIO;DESCRIZIONE;RICAMBI;ARTICOLI KIT;CONFIGURABILE' + "\n")
 f.close()
if not os.path.isfile(filecompatibilita):
 f=open(filecompatibilita,'a')
 f.write('SKU;MARCHIO MOTO;MODELLO MOTO;ANNI' + "\n")
 f.close() 
options=Options()
options.add_argument('headless')
options.add_argument('start-maximized')
browser=webdriver.Chrome(options=options)
contalink=int(0)
apri_elemento=int(0)
linkarticoli=[]
listamarchi_articoli=[]
link_articoli_configurabili=[]
listalink_apri=[]
def controlla_connessione(url='http://www.google.com/', timeout=5):
 try:
  _ = requests.get(url, timeout=timeout)
  return True
 except requests.ConnectionError:
  return False
def controllo_monitor(interval=1):
 while True:
  if not controlla_connessione():
   print("Connessione internet assente. Sospensione del programma...")
   while not controlla_connessione():
    time.sleep(interval)
  else:
   break      
linksito='https://www.maxiscoot.com/it'
controllo_monitor(interval=1)
browser.get(linksito)
link_fatto=set()
file_errori='DATI/errori.csv'
time.sleep(4)
contamarchio=int(0)
regola_regex=r"\([0129]*-*[0129]\)"
regola_apostrofo=r"\([^)]+\'([019][0-9]+).*?\)[^\)]*"
contamarchio_articolo=int(0)
browser.find_elements(By.CLASS_NAME,'cmpboxbtn.cmpboxbtnsave.cmptxt_btn_save')[0].click()
time.sleep(1)
fileinput='listalink.csv'
with open(fileinput,'r') as file:
 for riga in file:
  linkarticoli.append(riga.split(';')[1].strip())
  listamarchi_articoli.append(riga.split(';')[0].strip())  
for link in linkarticoli:
 controllo_monitor(interval=1)
 contalink=0
 configurabile=''   
 try:
  articolisuggeriti=''   
  articoli_kit=''   
  marchio_articolo=listamarchi_articoli[contamarchio_articolo]
  articolosuggerito=''
  browser.get(link)
  WebDriverWait(browser, 20).until(EC.presence_of_element_located((By.CLASS_NAME, "pvd_cb__sku")))
  if 'varid' not in link:
   try:
    numeroarticoli_configurabili=len(browser.find_element(By.ID,'pvd_vs_v1__select').find_elements(By.XPATH, "//option[@data-vid]"))
    for i in range(numeroarticoli_configurabili):
     if i > 0 : #SALTA LA PRIMA OPZIONE CHE E LA SCELTA
      linkarticolo_configurabile=link + '?varid=' + str(browser.find_element(By.ID,'pvd_vs_v1__select').find_elements(By.XPATH, "//option[@data-vid]")[i].get_attribute('data-vid'))
      link_articoli_configurabili.append(linkarticolo_configurabile)     
    link=link_articoli_configurabili[0]
   except Exception:
    pass
  articolo_links = [link] + link_articoli_configurabili 
  for articolo_link in articolo_links:   
   if articolo_link in link_fatto :
    continue
   if 'varid' in articolo_link:
    configurabile='X'
    contalink=contalink+1
   else:
    contalink=0    
   browser.get(articolo_link)
   WebDriverWait(browser, 20).until(EC.presence_of_element_located((By.CLASS_NAME, "pvd_cb__sku")))
   try:
    descrizione=browser.find_elements(By.CLASS_NAME,'pvd_pc__accordion_content.uk-accordion-content.uk-active')[0].get_attribute('innerText').replace("\n\n","\n").replace("\n",' | ').replace(';',',')
    sku=browser.find_elements(By.CLASS_NAME,'pvd_cb__sku')[contalink].get_attribute('innerText').replace('Riferimento:','').replace("\u00a0","")    
    print(sku)
   except Exception:
    pass
   try: 
    try:
     dati_tecnici=browser.find_elements(By.CLASS_NAME,'pvd_td__table')[contalink].get_attribute('innerHTML')
    except Exception:
     print('NO DATI TECNICI\n')  
    estrattore = BeautifulSoup(dati_tecnici, 'html.parser')
    righe=estrattore.find_all('tr', class_='pvd_td__row')
    dato=[]
    for riga in righe[1:]:
     intestazione=riga.find('th').text.strip()
     valore=riga.find('td')
     if valore:
      valore_cella=valore.text.strip()
     else: 
      valore_cella = None      
     dato.append({intestazione : valore_cella})
    df = pd.DataFrame(dato)
    df = df.ffill()
    df = df.iloc[-1]
    df = df.to_frame().T
    df = df.apply(
       lambda row: "$".join([f"{col}: {row[col]}" for col in df.columns]),
       axis=1
    )
    dati_tecnici_testo=pd.DataFrame(df, columns=["Formatted"])
    dati_tecnici_testo.to_csv(filedatitecnici, index=False, sep=";" , mode='a' , header=False)
   except Exception:
    f=open(file_errori,'a')
    f.write(sku + ';ERRORE DATI TECNICI' + "\n")
    f.close()   
   try:
    titolo=browser.find_elements(By.CLASS_NAME,'pvd_cb__product_name.artikel_detail__product_name')[0].get_attribute('innerText').replace(';',',')  
   except Exception:
    titolo=''
    f=open(file_errori,'a')
    f.write(sku + ';ERRORE RECUPERO TITOLO' + "\n")
    f.close()
   try:
    articolo_kit = browser.find_elements(By.XPATH, "//header[contains(@class, 'artikel_detail__section_title') and contains(@class, 'artikel_detail__section_title--1') and contains(@class, 'pvd_pl__title') and contains(text(), 'Componenti')]/..")[0]     
    if articolo_kit:
     numeroarticoli_kit=len(articolo_kit.find_elements(By.CLASS_NAME,'element_product_grid.element_product_grid--cw')[0].find_elements(By.CLASS_NAME,'element_artikel'))
     for j in range(numeroarticoli_kit):
      articolo_kit_singolo=articolo_kit.find_elements(By.CLASS_NAME,'element_product_grid.element_product_grid--cw')[0].find_elements(By.CLASS_NAME,'element_artikel')[j].get_attribute('data-sku').replace(';','')        
      articoli_kit=articoli_kit+articolo_kit_singolo+'$'
   except Exception:       
    articoli_kit=''  
   try:
    numero_articolisuggeriti=len(browser.find_elements(By.CLASS_NAME,'element_productslider.uk-slidenav-position.deprecated.element-slider-products.element_productslider.artikel_detail__section_content.pvd_xr_accessory__content')[0].find_elements(By.CLASS_NAME,'element_productslider__slider.uk-slider.uk-grid')[0].find_elements(By.TAG_NAME,'li'))
   except Exception:
    numero_articolisuggeriti=0   
   if numero_articolisuggeriti >= 1 :
    for j in range(numero_articolisuggeriti):   
     articolosuggerito=browser.find_elements(By.CLASS_NAME,'element_productslider.uk-slidenav-position.deprecated.element-slider-products.element_productslider.artikel_detail__section_content.pvd_xr_accessory__content')[0].find_elements(By.CLASS_NAME,'element_productslider__slider.uk-slider.uk-grid')[0].find_elements(By.TAG_NAME,'li')[j].find_elements(By.TAG_NAME,'a')[0].get_attribute('data-sku').replace(';',',')
     articolisuggeriti=articolisuggeriti+articolosuggerito+'$'
   else:
    articolisuggeriti=''      
   #BLOCCO FOTO
   try:
    tipofoto=len(browser.find_elements(By.CLASS_NAME,'element_swiperjs__button_next.swiper-button-next'))   
    if tipofoto > 0 :
     browser.find_elements(By.CLASS_NAME,'pvd_mb__slide.pvd_mb__slide--image.swiper-slide.pvd_mb__slide--lightbox.js_pvd_mb__slide_zoom.swiper-slide-active')[0].click()
     time.sleep(1)
     WebDriverWait(browser, 20).until(EC.presence_of_element_located((By.CLASS_NAME, "lg-next.lg-icon")))
     numerofoto=len(browser.find_elements(By.CLASS_NAME,'lg-thumb-item'))
     for i in range(numerofoto):
      if i == 0:
       linkfoto=browser.find_elements(By.CLASS_NAME,'lg-item.lg-next-slide.lg-prev-slide.lg-loaded.lg-current.lg-complete.lg-zoomable')[0].find_elements(By.CLASS_NAME,'lg-object.lg-image')[0].get_attribute('src')
      else:
       WebDriverWait(browser, 20).until(EC.presence_of_element_located((By.CLASS_NAME, "lg-next.lg-icon")))
       linkfoto=browser.find_elements(By.CLASS_NAME,'lg-item.lg-loaded.lg-complete.lg-zoomable.lg-next-slide.lg-current')[0].find_elements(By.CLASS_NAME,'lg-object.lg-image')[0].get_attribute('src')   
      browser.find_elements(By.CLASS_NAME,'lg-next.lg-icon')[0].click()
      WebDriverWait(browser, 20).until(EC.presence_of_element_located((By.CLASS_NAME, "lg-next.lg-icon")))
      time.sleep(0.5)
      f=open(filefoto,'a')
      f.write(sku + ';' + str(i+1) + ';' + linkfoto + "\n")
      f.close()  
    if tipofoto == 0:
     try:
      browser.find_elements(By.CLASS_NAME,'pvd_mb__slide.pvd_mb__slide--image.uk-width-1-1.pvd_mb__slide--lightbox.js_pvd_mb__slide_zoom')[0].click()
      WebDriverWait(browser, 20).until(EC.presence_of_element_located((By.CLASS_NAME, "lg-object.lg-image")))
      linkfoto=browser.find_elements(By.CLASS_NAME,'lg-object.lg-image')[0].get_attribute('src')
      f=open(filefoto,'a')
      f.write(sku + ';1;' + linkfoto + "\n") 
     except Exception:
      traceback.print_exc()   
   except Exception:
    f=open(file_errori,'a')
    f.write(sku + ';ERRORE RECUPERO FOTO' + "\n")
    f.close()  
   #FINE BLOCCO FOTO INIZIO BLOCCO COMPATIBILITA
   try:
    numeromarchi=len(browser.find_elements(By.CLASS_NAME,'pvd_sf__accordion_wrapper.et_accordion'))
    for x in range(numeromarchi):
     marchiomoto=''
     marchiomoto=browser.find_elements(By.CLASS_NAME,'pvd_sf__accordion_wrapper.et_accordion')[x].find_elements(By.CLASS_NAME,'pvd_sf__accordion_title.et_accordion_title')[0].get_attribute('innerText')
     numero_modellimoto=len(browser.find_elements(By.CLASS_NAME,'pvd_sf__accordion_wrapper.et_accordion')[x].find_elements(By.CLASS_NAME,'pvd_sf__model'))
     for j in range(numero_modellimoto):
      modellomoto=''
      anni=''
      modellomoto=browser.find_elements(By.CLASS_NAME,'pvd_sf__accordion_wrapper.et_accordion')[x].find_elements(By.CLASS_NAME,'pvd_sf__model')[j].get_attribute('innerText')   
      if modellomoto == '':
       modellomoto=browser.find_elements(By.CLASS_NAME,'pvd_sf__accordion_wrapper.et_accordion')[x].find_elements(By.CLASS_NAME,'pvd_sf__model')[j].get_attribute('innerHTML')   
      controllo_1=re.search(regola_regex, modellomoto)
      controllo_2=re.findall(regola_apostrofo, modellomoto)
      controllo_2="".join(controllo_2)
      try:
       if controllo_1 :
        anno_da = modellomoto.split('(')[1].split('-')[0].split(')')[0].replace(' ','')
        anno_a =  modellomoto.split('(')[1].split('-')[1].split(')')[0].replace(' ','')
        anni=anno_da+'-'+anno_a
       if controllo_2 and not controllo_1:
        stringa_prima=modellomoto.split("'"+controllo_2)[0].split('(')[1].strip()
        if stringa_prima == 'dopo il' or stringa_prima == 'dal':
         if controllo_2[0] == '9':
          anni=('19' + controllo_2 +'-')
         if controllo_2[0] == '0':
          anni=('20' + controllo_2 + '-')
        if stringa_prima == 'prima del' or stringa_prima == 'fino al' or stringa_prima == 'fino a':
         if controllo_2[0] == '9':
          anni=('-19' + controllo_2 )
         if controllo_2[0] == '0':
          anni=('-20' + controllo_2 )            
      except Exception:
       anni=''   
      f=open(filecompatibilita,'a')
      f.write(sku + ';' + marchiomoto + ';' + modellomoto + ';' + anni + " \n")    
      f.close()
   except Exception:
    traceback.print_exc()   
    f=open(file_errori,'a')
    f.write(sku + ';ERRORE RECUPERO COMPATIBILITA' + "\n")
    f.close()
    #FINE BLOCCO COMPATIBILITA 
   f=open(fileanagrafica,'a')
   f.write(f"{sku};{titolo};{marchio_articolo};{descrizione};{articolisuggeriti};{articoli_kit};{configurabile};\n") 
   f.close()
   contamarchio_articolo = contamarchio_articolo + 1
   link_fatto.add(articolo_link)
 except Exception:
  f=open(file_errori,'a')
  f.write(link + ';ERRORE RECUPERO ARTICOLO' + "\n")
  f.close()
  browser.get(linksito)
  time.sleep(10)
  