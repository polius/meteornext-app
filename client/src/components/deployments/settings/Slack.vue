<template>
  <div>
    <v-card>
      <v-toolbar flat color="primary">
        <v-toolbar-title>SLACK</v-toolbar-title>
      </v-toolbar>
      <v-container fluid grid-list-lg>
        <v-layout row wrap>
          <v-flex xs12>
            <v-text-field v-model="webhook" label="Webhook URL" required></v-text-field>
            <v-switch v-model="enabled" label="Enable Notifications" style="margin-top:0px;"></v-switch>
            <v-btn color="primary" style="margin-left:0px;" @click="save()">Save</v-btn>
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
    webhook: '',
    enabled: false,

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