<template>
  <v-slide-y-transition mode="out-in">
    <v-container fluid>
      <v-content>
        <v-card>
          <v-toolbar flat color="primary">
            <v-toolbar-title>PROFILE</v-toolbar-title>
          </v-toolbar>
          <v-container fluid grid-list-lg>
            <v-layout row wrap>
              <v-flex xs12>
                <div class="headline font-weight-regular">Hello <b>palzina</b> <v-chip color="primary" text-color="white" style="margin-left:10px;">ADMINISTRATOR</v-chip></div>
                <v-text-field v-model="email" label="Email" type="email" append-icon="email" style="margin-top:10px;"></v-text-field>
                <v-text-field v-model="password" label="Password" type="password" append-icon="lock" style="padding-top:0px;"></v-text-field>
                <v-btn color="primary" @click="save()" style="margin-left:0px;">Save</v-btn>    
              </v-flex>
            </v-layout>
          </v-container>
        </v-card>

        <v-snackbar v-model="snackbar" :timeout="snackbarTimeout" :color="snackbarColor" top>
          {{ snackbarText }}
          <v-btn color="white" text @click="snackbar = false">Close</v-btn>
        </v-snackbar>
      </v-content>
    </v-container>
  </v-slide-y-transition>
</template>

<script>
// import axios from 'axios';

export default {
  data: () => ({
    email: 'palzina@inbenta.com',
    password: '1234567890',

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