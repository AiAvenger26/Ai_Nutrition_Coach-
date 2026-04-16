const express = require('express');
const cors = require('cors');
const app = express();
app.use(cors());
app.use(express.json());
app.use(express.static('static'));
app.use('/templates', express.static('templates'));

app.get('/', (req, res) => {
  res.send('AI Nutrition Coach Backend Running - Visit http://localhost:5000');
});

app.listen(5000, () => {
  console.log('Server running on http://localhost:5000');
});
