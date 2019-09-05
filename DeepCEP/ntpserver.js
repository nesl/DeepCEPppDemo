const express = require('express')
const app = express()
const port = 80

app.get('/', (request, response) => {
  response.status(200).send((new Date()).getTime().toString());
})

app.listen(port, (err) => {
  if (err) {
    return console.log('something bad happened', err)
  }

  console.log(`server is listening on ${port}`)
})
