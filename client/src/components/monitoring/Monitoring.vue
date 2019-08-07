<template>
  <div>
    <v-layout style="margin-left:8px; margin-right:8px;">
      <v-flex xs3 v-for="item in links" :key="item.id" style="margin:5px;">
        <v-hover>
          <v-card slot-scope="{ hover }" :class="`elevation-${hover ? 12 : 2}`">
            <v-img height="10px" :class="item.color"></v-img>
            <v-card-title primary-title style="padding-bottom:5px;">
              <p class="title text-xs-center">{{item.title}}</p>
            </v-card-title>
            <v-divider></v-divider>
            <v-card-text>
              <p class="subheading">Hostname: </p>
              <p class="subheading">Uptime: </p>
              <p class="subheading">Connections: </p>
            </v-card-text>
          </v-card>
        </v-hover>
      </v-flex>      
    </v-layout>
  </div>
</template>

<script>
  export default {
    data() {
      return {
        links: [
          {
            id: '1',
            title: 'Templates EU',
            color: 'teal'
          },
          {
            id: '2',
            title: 'Templates US',
            color: 'red'
          },
          {
            id: '3',
            title: 'Templates JP',
            color: 'orange'
          },
          {
            id: '4',
            title: 'Aurora Apps',
            color: 'teal'
          }      
        ]
      }
    }
  }
</script>