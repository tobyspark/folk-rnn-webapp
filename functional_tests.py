from selenium import webdriver

browser = webdriver.Firefox()

# Ada navigates to the folk_rnn web app
browser.get('http://localhost:8000')

# Sees that it is indeed about the folk-rnn folk music style modelling project
assert 'Folk RNN' in browser.title

# Sees a compose tune section at the top of the page, hits "compose"

# Compose section changes to "composition in process"

# Eventually, the compose section changes again, displaying the tune in ABC notation.
# There is also a button to reset and compose again. Which she presses, and the 
# compose section is as it was on first load.

browser.quit()