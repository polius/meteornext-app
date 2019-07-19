<template>
  <div>
    <v-toolbar color="primary" dark>
      <v-toolbar-title>AMAZON S3</v-toolbar-title>
    </v-toolbar>

    <v-card>
      <v-container fluid grid-list-lg>
        <v-layout row wrap>
          <v-flex xs12>
            <v-text-field v-model="aws_access_key" label="AWS Access Key" dark style="padding-top:0px;"></v-text-field>
            <v-text-field v-model="aws_secret_access_key" label="AWS Secret Access Key" dark></v-text-field>
            <v-text-field v-model="region_name" label="Region Name" hint="Example: eu-west-1" dark></v-text-field>
            <v-text-field v-model="bucket_name" label="Bucket Name" dark></v-text-field>
            <v-switch v-model="enabled" label="Enable Uploading Logs" style="margin-top:0px;"></v-switch>
            <v-btn color="primary" @click="save()" dark style="margin-left:0px;">Save</v-btn>    
          </v-flex>
        </v-layout>
      </v-container>
    </v-card>

    <v-snackbar v-model="snackbar" :timeout="snackbarTimeout" :color="snackbarColor" top>
      {{ snackbarText }}
      <v-btn color="white" flat @click="snackbar = false">Close</v-btn>
    </v-snackbar>
  </div>
</template>

<script>
import axios from 'axios';

export default {
  data: () => ({
    aws_access_key: '',
    aws_secret_access_key: '',
    region_name: '',
    bucket_name: '',
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