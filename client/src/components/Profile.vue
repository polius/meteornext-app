<template>
  <v-container fluid>
    <v-layout row wrap>
      <v-content style="padding-top:0px;">
        <v-slide-y-transition mode="out-in">
          <div>
          
            <v-toolbar color="primary" dark style="margin-top:60px;">
              <v-toolbar-title>PROFILE</v-toolbar-title>
            </v-toolbar>

            <v-card>
              <v-container fluid grid-list-lg>
                <v-layout row wrap>
                  <v-flex xs12>
                    <div class="headline font-weight-regular">Hello <b>palzina</b> <v-chip color="primary" text-color="white" style="margin-top:0px;">ADMINISTRATOR</v-chip></div>
                    <v-text-field v-model="email" label="Email" type="email" dark append-icon="email" style="margin-top:10px;"></v-text-field>
                    <v-text-field v-model="password" label="Password" dark type="password" append-icon="lock" style="padding-top:0px;"></v-text-field>
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
        </v-slide-y-transition>
      </v-content>
    </v-layout>
  </v-container>
</template>

<script>
import axios from 'axios';

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