<template>
  <div>
    <v-card>
      <v-toolbar dense flat color="primary">
        <v-toolbar-title class="body-2 white--text font-weight-medium"><v-icon small style="margin-right:10px">fas fa-bolt</v-icon>CLIENT</v-toolbar-title>
        <v-divider class="mx-3" inset vertical></v-divider>
        <v-toolbar-items class="hidden-sm-and-down">
          <v-btn text class="body-2"><v-icon small style="padding-right:10px">fas fa-search</v-icon>FILTER</v-btn>
          <v-btn text class="body-2"><v-icon small style="margin-right:10px">fas fa-sync-alt</v-icon>REFRESH</v-btn>
          <v-divider class="mx-3" inset vertical></v-divider>
          <v-btn text class="body-2"><v-icon small style="padding-right:10px">fas fa-database</v-icon>SERVERS</v-btn>
          <v-divider class="mx-3" inset vertical></v-divider>
        </v-toolbar-items>
        <v-text-field append-icon="search" label="Search" color="white" single-line hide-details></v-text-field>
      </v-toolbar>
    </v-card>
  </div>
</template>