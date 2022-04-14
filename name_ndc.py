import requests
import pandas as pd


def get_drugs(name : str, showcall = True):
    """
    Given a string containing a drug name, get the info returned by rxnav drugs endpoint for that search. 
    RxNav is kind of precious about formatting, so a single drug name works best
    """
    url = "https://rxnav.nlm.nih.gov/REST/drugs.json"
    querystring = {"name":name}
    response = requests.request("GET", url, params=querystring)
    if showcall:
        print(response.request.url)
    r = response.json()
    return r


"""
get_drugs('dasabuvir') will call https://rxnav.nlm.nih.gov/REST/drugs.json?name=dasabuvir 
and return something like the following, which get_drug_product_rxcuis must parse out

{
  "drugGroup": {
    "name": null,
    "conceptGroup": [
      {
        "tty": "BPCK",
        "conceptProperties": [
          {
            "rxcui": "1597388",
            "name": "{2 (dasabuvir 250 MG Oral Tablet) / 2 (ombitasvir 12.5 MG / paritaprevir 75 MG / ritonavir 50 MG Oral Tablet) } Pack [Viekira Pak]",
            ....
          }]},
...
      {
        "tty": "SBD"
      },
...     ]}}
"""

def get_drug_product_concept_properties(name : str):
    """
    Search get_drugs, get the properties for matching concepts
    """

    # clinical drug (SCD), clinical pack (GPCK), branded drug (SBD), branded pack (BPCK)
    types = ('SCD', 'GPCK', 'SBD', 'BPCK')
    r = get_drugs(name)
    props = [group['conceptProperties']
              for group in r['drugGroup']['conceptGroup']
              # Note that a concept group may have a type but be otherwise empty
              if group['tty'] in types and group.get('conceptProperties', [])]

    return props

def get_ndcs_from_rxcui(rxcui : str):
    """
    Given an rxcui, get matching ndcs
    """
    url = f"https://rxnav.nlm.nih.gov/REST/rxcui/{rxcui}/ndcs.json"
    response = requests.request("GET", url)    
    r = response.json()
    try:
        return r['ndcGroup']['ndcList']['ndc']
    except KeyError:
        # if there's no ndc, return the empty list
        return []




def get_drug_product_df(name : str) -> pd.DataFrame:
    """
    Given a string containing a drug name, get matching properties, including RxCUIs, and associated NDCs. 
    Return as a DataFrame.
    """
    groups  = get_drug_product_concept_properties(name)
    df = pd.concat([pd.DataFrame(g) for g in groups])
    df['ndcs'] = df.apply(lambda x : get_ndcs_from_rxcui(x.rxcui), axis = 1)
    df['search'] = name
    return df


"""
E.g. build a spreadsheet
ty = search_drug_names(['tylenol'])
ty.to_excel('ty.xlsx')
"""
def search_drug_names(names : list[str]) -> pd.DataFrame:
    return pd.concat([get_drug_product_df(n) for n in names])

