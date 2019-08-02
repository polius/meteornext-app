<template>
  <div>
    <v-card>
      <v-toolbar flat color="primary">
        <v-toolbar-title>WEB</v-toolbar-title>
      </v-toolbar>
      <v-container fluid grid-list-lg>
        <v-layout row wrap>
          <v-flex xs12>
            <v-text-field v-model="public_url" label="Public Web URL" required></v-text-field>
            <v-btn color="primary" @click="save()" style="margin-left:0px;">Save</v-btn>    
          </v-flex>
        </v-layout>
      </v-container>
    </v-card>

    <v-snackbar v-model="snackbar" :timeout="snackbarTimeout" :color="snackbarColor" top>
      {{ snackbarText }}
      <v-btn color="white" text @click="snackbar = false">Close</v-btn>
    </v-snackbar>
  </div>
</template>

<script>
// import axios from 'axios';

export default {
  data: () => ({
    public_url: '',

    // Snackbar
    snackbar: false,
    snackbarTimeout: Number(3000),
    snackbarColor: '',
    snackbarText: ''
  }),
  methods: {
    save() {
      this.notification('Changes saved successfully', 'success')
    },
    notification(message, color) {
      this.snackbarText = message
      this.snackbarColor = color 
      this.snackbar = true
    }
  }
}
</script>