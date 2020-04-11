<template>
  <div>
    <v-card style="margin-bottom:7px;">
      <v-toolbar dense flat color="primary">
        <v-toolbar-title class="white--text">MONITORING</v-toolbar-title>
        <v-divider class="mx-3" inset vertical></v-divider>
        <v-toolbar-items class="hidden-sm-and-down">
          <v-btn text title="Settings" ><v-icon small style="padding-right:10px">fas fa-cog</v-icon>SETTINGS</v-btn>
        </v-toolbar-items>
        <v-spacer></v-spacer>
        <div class="subheading font-weight-regular" style="padding-right:10px;">Updated on <b>{{ dateFormat(last_updated) }}</b></div>
      </v-toolbar>
    </v-card>

    <v-layout style="margin-left:-4px; margin-right:-4px;">
      <v-flex xs3 v-for="item in links" :key="item.id" style="margin:5px; cursor:pointer;" @click="monitor(item)">
        <v-hover>
          <v-card slot-scope="{ hover }" :class="`elevation-${hover ? 12 : 2}`">
            <v-img height="10px" :class="item.color"></v-img>
            <v-card-title primary-title style="padding-bottom:10px;">
              <p class="text-xs-center" style="margin-bottom:0px;">
                <span class="title">{{item.title}}</span>
                <br>
                <span class="body-2">{{item.region}}</span>
              </p>
            </v-card-title>
            <v-divider></v-divider>
            <v-card-text style="padding-bottom:1px;">
              <p class="font-weight-medium">Hostname<pre>127.0.0.1</pre></p>
              <p class="font-weight-medium">Connections<pre>23</pre></p>
            </v-card-text>
          </v-card>
        </v-hover>
      </v-flex>      
    </v-layout>
  </div>
</template>

<script>
  // import axios from 'axios'
  import moment from 'moment'

  export default {
    data() {
      return {
        last_updated: '2020-01-01 20:12:23',
        links: [
          { id: '1', title: 'Templates EU', region: 'AWS-EU', color: 'teal' },
          { id: '2', title: 'Templates US', region: 'AWS-US', color: 'red' },
          { id: '3', title: 'Templates JP', region: 'AWS-JP', color: 'orange' },
          { id: '4', title: 'Aurora Apps', region: 'AWS-EU', color: 'teal' }      
        ]
      }
    },
    methods: {
      monitor(item) {
        this.$router.push({ name:'monitor', params: { id: item.id }})
        console.log(item)
      },
      dateFormat(date) {
        if (date) return moment.utc(date).local().format("YYYY-MM-DD HH:mm:ss")
        return date
      }
    }
  }
</script>