<template>
  <div>
    <v-card style="margin-bottom:7px;">
      <v-toolbar dense flat color="#3a529b">
        <v-toolbar-title class="body-2 white--text font-weight-medium"><v-icon small style="margin-right:10px">fas fa-layer-group</v-icon>INVENTORY</v-toolbar-title>
        <v-divider class="mx-3" inset vertical></v-divider>
        <v-toolbar-items class="hidden-sm-and-down">
          <v-btn text class="body-2">ENVIRONMENTS</v-btn>
          <v-divider class="mx-3" inset vertical></v-divider>
          <v-btn text class="body-2">REGIONS</v-btn>
          <v-divider class="mx-3" inset vertical></v-divider>
          <v-btn text class="body-2">SERVERS</v-btn>
          <v-divider class="mx-3" inset vertical></v-divider>
          <v-btn text class="body-2">AUXILIARY CONNECTIONS</v-btn>
          <v-divider class="mx-3" inset vertical></v-divider>
        </v-toolbar-items>
      </v-toolbar>
      <!-- v-data-table -->
    </v-card>
  </div>
</template>