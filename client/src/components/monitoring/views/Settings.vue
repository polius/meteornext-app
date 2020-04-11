<template>
  <div>
    <v-card>
      <v-toolbar flat color="primary">
        <v-toolbar-title class="white--text">SETTINGS</v-toolbar-title>
        <v-spacer></v-spacer>
        <v-btn icon title="Go back" @click="goBack()"><v-icon>fas fa-arrow-alt-circle-left</v-icon></v-btn>
      </v-toolbar>

      <v-card-text>
        <!-- MONITOR - BAR -->
        <div>
          <v-tabs show-arrows background-color="#263238" color="white" v-model="tabs" slider-color="white" slot="extension" class="elevation-2">
            <v-tabs-slider></v-tabs-slider>
            <v-tab><span class="pl-2 pr-2">MONITORING</span></v-tab>
            <v-divider class="mx-3" inset vertical></v-divider>
            <v-tab><span class="pl-2 pr-2">PARAMETERS</span></v-tab>
            <v-divider class="mx-3" inset vertical></v-divider>
            <v-tab><span class="pl-2 pr-2">PROCESSLIST</span></v-tab>
            <v-divider class="mx-3" inset vertical></v-divider>
            <v-tab><span class="pl-2 pr-2">QUERIES</span></v-tab>
          </v-tabs>
        </div>

        <!-- SUMMARY -->
        <div v-show="tabs == 0" style="margin-top:10px;">
          <div class="title font-weight-regular white--text" style="margin-bottom:5px;">INFO</div>
        </div>

        <!-- LOGS -->
        <v-card v-show="tabs == 1">
          
        </v-card>

        <!-- CONNECTIONS -->
        <v-card v-show="tabs == 2">

        </v-card>

        <!-- STATEMENTS -->
        <v-card v-show="tabs == 3">

        </v-card>

        <!-- INDEXES -->
        <v-card v-show="tabs == 4">

        </v-card>

        <!-- RDS METRICS -->
        <v-card v-show="tabs == 5">

        </v-card>
      </v-card-text>
    </v-card>

    <v-snackbar v-model="snackbar" :timeout="snackbarTimeout" :color="snackbarColor" top>
      {{ snackbarText }}
      <v-btn color="white" text @click="snackbar = false">Close</v-btn>
    </v-snackbar>
  </div>
</template>

<script>
// import axios from 'axios'

export default {
  data: () => ({
    tabs: 0,

    // Snackbar
    snackbar: false,
    snackbarTimeout: Number(3000),
    snackbarText: '',
    snackbarColor: ''
  })
}
</script>